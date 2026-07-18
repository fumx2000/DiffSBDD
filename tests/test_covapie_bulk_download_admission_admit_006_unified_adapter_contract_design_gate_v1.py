from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_admit_006_unified_adapter_contract_design_gate as gate,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "scripts/check_covapie_bulk_download_admission_admit_006_unified_adapter_contract_design_gate_v1.py"
OUTPUT_ROOT = ROOT / gate.DEFAULT_OUTPUT_ROOT


def _rows(filename: str) -> list[dict[str, str]]:
    with (OUTPUT_ROOT / filename).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _routing(case_id: str) -> dict[str, str]:
    return next(row for row in _rows(gate.ROUTING_FILENAME) if row["case_id"] == case_id)


def _truth(case_id: str) -> dict[str, str]:
    return next(row for row in _rows(gate.TRUTH_FILENAME) if row["case_id"] == case_id)


def _valid_source() -> gate.Admit006EvaluationDesignRecord:
    return gate.classify_admit_006_independent_design(
        "explicit_structure_bond_record", gate.ALLOWED_CLASSES
    )


@pytest.mark.parametrize("case_id", ["candidate_key_missing", "candidate_exact_none", "candidate_builtin_empty"])
def test_adapter_missing_paths_do_not_call_evaluator_or_oracle(case_id: str) -> None:
    row = _routing(case_id)
    assert row["expected_reason"] == gate.MISSING_REASON
    assert (row["formal_call_count"], row["oracle_call_count"]) == ("0", "0")
    result = json.loads(row["expected_result_json"])
    assert result["normalized_values"] == result["validated_candidate_fields"] == []


@pytest.mark.parametrize(
    ("case_id", "reason"),
    [
        ("empty_str_subclass", gate.SCALAR_REASONS[0]),
        ("whitespace_not_missing", gate.SCALAR_REASONS[3]),
        ("distance_not_missing", gate.BLOCKED_REASON),
    ],
)
def test_nonmissing_values_are_routed_to_standalone(case_id: str, reason: str) -> None:
    row = _routing(case_id)
    assert row["expected_reason"] == reason
    assert (row["formal_call_count"], row["oracle_call_count"]) == ("1", "1")


def test_invalid_routed_context_value_is_not_dispatch_error() -> None:
    row = _routing("invalid_value_reaches_standalone")
    assert row["expected_behavior"] == "exact13_invalid_not_dispatch"
    assert json.loads(row["expected_result_json"])["outcome"] == "invalid"


@pytest.mark.parametrize("case_id", ["evaluation_non_mapping", "evaluation_key_missing"])
def test_evaluation_envelope_failures_are_exact6(case_id: str) -> None:
    row = _routing(case_id)
    assert row["expected_behavior"] == "dispatch_error"
    assert json.loads(row["expected_result_json"])["code"] == "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"


def test_candidate_is_not_accessed_before_context_routing() -> None:
    for case in ("batch_non_none", "evaluation_non_mapping", "evaluation_key_missing", "multiple_failure_precedence"):
        assert _routing(case)["candidate_access_status"] == "not_accessed"


def test_context_failure_precedence_is_frozen() -> None:
    assert _routing("multiple_failure_precedence")["expected_reason"] == gate.CONTEXT_REASONS["batch_context"]


def test_source_subclass_is_rejected() -> None:
    class Subclass(gate.Admit006EvaluationDesignRecord):
        pass

    source = _valid_source()
    subclass = Subclass(*(getattr(source, name) for name in gate.STANDALONE_RESULT_FIELDS))
    decision = gate.validate_source_shape_and_invariants_for_design(subclass)
    assert not decision.accepted and decision.reason == gate.SOURCE_TYPE_REASON


@pytest.mark.parametrize("source", [object(), None, {"outcome": "passed"}])
def test_wrong_source_type_is_rejected(source: object) -> None:
    decision = gate.validate_source_shape_and_invariants_for_design(source)
    assert not decision.accepted and decision.adapter_ready is False


@pytest.mark.parametrize(
    "mutation",
    [
        {"admission_rule_id": "ADMIT_005"},
        {"outcome": "rejected"},
        {"passed": False},
        {"blocks_candidate": True},
        {"reason": "COVALENT_EVENT_EVIDENCE_SOURCE_UNKNOWN"},
        {"canonical_covalent_event_evidence_source": ""},
        {"validated_candidate_fields": ()},
        {"consumed_candidate_fields": ()},
        {"consumed_context_items": ()},
        {"evaluator_io_used": True},
    ],
)
def test_source_cross_field_invariant_mutations_fail(mutation: dict[str, object]) -> None:
    decision = gate.validate_source_shape_and_invariants_for_design(replace(_valid_source(), **mutation))
    assert not decision.accepted and decision.reason == gate.SOURCE_INVARIANT_REASON


def test_source_prevalidation_short_circuits_before_expected_oracle_access() -> None:
    class Bomb:
        def __getattribute__(self, name: str) -> object:
            raise AssertionError("oracle evidence accessed before source prevalidation")

    decision = gate.validate_source_oracle_equivalence_for_design(object(), Bomb())
    assert decision.reason == gate.SOURCE_TYPE_REASON


def test_oracle_mismatch_blocks_projection() -> None:
    source = _valid_source()
    expected = gate.classify_admit_006_independent_design("explicit_curated_covalent_annotation", gate.ALLOWED_CLASSES)
    decision = gate.validate_source_oracle_equivalence_for_design(source, expected)
    assert not decision.accepted and decision.reason == gate.SOURCE_INVARIANT_REASON


def test_blocked_outcome_is_passed_through() -> None:
    result = json.loads(_truth("PROJECTION_distance_blocked")["unified_exact13_json"])
    assert result["outcome"] == "blocked"
    assert result["reason"] == gate.BLOCKED_REASON
    assert result["normalized_values"] == [[gate.CANDIDATE_FIELDS[0], "distance_only_inference"]]


def test_context_invalid_retains_canonical_pair() -> None:
    result = json.loads(_truth("PROJECTION_context_invalid_canonical_retained")["unified_exact13_json"])
    assert result["outcome"] == "invalid"
    assert result["normalized_values"] == result["validated_candidate_fields"] != []


def test_candidate_invalid_retains_consumed_context_item() -> None:
    result = json.loads(_routing("candidate_non_mapping")["expected_result_json"])
    assert result["consumed_context_items"] == list(gate.CONTEXT_ITEMS)


def test_issue_inventory_is_exact11_and_byte_identical() -> None:
    predecessor = ROOT / gate.SOURCE_PATHS[4]
    generated = OUTPUT_ROOT / gate.ISSUE_FILENAME
    assert generated.read_bytes() == predecessor.read_bytes()
    assert len(_rows(gate.ISSUE_FILENAME)) == 11


def test_coverage_issue_still_contains_admit006() -> None:
    issues = {row["issue_id"]: row for row in _rows(gate.ISSUE_FILENAME)}
    assert "ADMIT_006" in issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"].split("|")


def test_current_runtime_is_exact5_and_has_no_admit006_handler() -> None:
    manifest = json.loads((ROOT / gate.SOURCE_PATHS[11]).read_text())
    assert manifest["registered_rule_ids"] == list(gate.CURRENT_REGISTERED_RULE_ORDER)
    tree = ast.parse((ROOT / gate.SOURCE_PATHS[10]).read_text())
    assert "_evaluate_registered_admit_006" not in {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_production_is_standard_library_only_and_has_no_runtime_handler() -> None:
    tree = ast.parse(Path(gate.__file__).read_text())
    imports = {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert "covalent_ext" not in imports
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert "evaluate_admission_rule" not in functions and "_evaluate_registered_admit_006" not in functions


def test_standalone_evaluator_ast_does_not_call_design_oracle() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    tree = ast.parse(gate._bytes(snapshot, gate.SOURCE_PATHS[0]).decode())
    assert gate.INDEPENDENT_ORACLE_NAME not in gate._function_calls(tree, gate.FORMAL_EVALUATOR_NAME)


def test_exact37_projection_and_natural_group_counts() -> None:
    rows = _rows(gate.TRUTH_FILENAME)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["case_group"]] = counts.get(row["case_group"], 0) + 1
    assert counts == {"standalone_exact37": 37, "adapter_candidate_invalid": 4, "routing_dispatch": 5,
                      "source_validation_failure": 4, "projection_semantics": 4, "runtime_boundary": 2}


def test_deterministic_double_materialization(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    gate.run_covapie_bulk_download_admission_admit_006_unified_adapter_contract_design_gate_v1(first)
    gate.run_covapie_bulk_download_admission_admit_006_unified_adapter_contract_design_gate_v1(second)
    assert all((first / name).read_bytes() == (second / name).read_bytes() for name in gate.OUTPUT_FILES)


def test_tamper_fails_even_if_manifest_hash_is_refreshed(tmp_path: Path) -> None:
    expected, tampered = tmp_path / "expected", tmp_path / "tampered"
    gate.run_covapie_bulk_download_admission_admit_006_unified_adapter_contract_design_gate_v1(expected)
    gate.run_covapie_bulk_download_admission_admit_006_unified_adapter_contract_design_gate_v1(tampered)
    target = tampered / gate.CONTRACT_FILENAME
    target.write_bytes(target.read_bytes() + b"tamper\n")
    manifest_path = tampered / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text())
    manifest["output_sha256"][gate.CONTRACT_FILENAME] = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    checker = _load_checker()
    with pytest.raises(AssertionError, match="Exact43 contract rows mismatch"):
        checker._validate_output_tree(tampered, enforce_frozen_hashes=False)


def _load_checker():
    spec = importlib.util.spec_from_file_location("admit006_checker_for_test", CHECKER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("mode", ["missing", "extra", "symlink"])
def test_missing_extra_or_symlink_output_fails_closed(tmp_path: Path, mode: str) -> None:
    expected, candidate = tmp_path / "expected", tmp_path / "candidate"
    gate.run_covapie_bulk_download_admission_admit_006_unified_adapter_contract_design_gate_v1(expected)
    gate.run_covapie_bulk_download_admission_admit_006_unified_adapter_contract_design_gate_v1(candidate)
    if mode == "missing":
        (candidate / gate.CONTRACT_FILENAME).unlink()
    elif mode == "extra":
        (candidate / "unexpected.txt").write_text("x")
    else:
        victim = candidate / gate.CONTRACT_FILENAME
        victim.unlink()
        victim.symlink_to(expected / gate.CONTRACT_FILENAME)
    with pytest.raises(AssertionError):
        _load_checker()._validate_output_tree(candidate, expected_materialized=expected)


def test_source_sha_mismatch_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    altered = dict(gate.SOURCE_SHA256)
    altered[gate.SOURCE_PATHS[0]] = "0" * 64
    monkeypatch.setattr(gate, "SOURCE_SHA256", altered)
    with pytest.raises(ValueError, match="source SHA256 mismatch"):
        gate.build_frozen_source_snapshot()


def test_non_descendant_base_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not an ancestor"):
        gate.build_frozen_source_snapshot(head_ref=f"{gate.EXPECTED_BASE_COMMIT}^")


def test_symlink_source_victim_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    victim = tmp_path / "victim"
    victim.write_text("x")
    link = tmp_path / "link"
    link.symlink_to(victim)
    monkeypatch.setattr(gate, "_git", lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="blob\n"))
    with pytest.raises(ValueError, match="regular non-symlink"):
        gate._structural_check(Path("link"), tmp_path)


def test_unexpected_existing_output_entry_fails_closed(tmp_path: Path) -> None:
    tmp_path.mkdir(exist_ok=True)
    (tmp_path / "unexpected").write_text("x")
    with pytest.raises(ValueError, match="unexpected output entry"):
        gate.run_covapie_bulk_download_admission_admit_006_unified_adapter_contract_design_gate_v1(tmp_path)


def test_manifest_overclaim_fails_checker(tmp_path: Path) -> None:
    expected, candidate = tmp_path / "expected", tmp_path / "candidate"
    gate.run_covapie_bulk_download_admission_admit_006_unified_adapter_contract_design_gate_v1(expected)
    gate.run_covapie_bulk_download_admission_admit_006_unified_adapter_contract_design_gate_v1(candidate)
    path = candidate / gate.MANIFEST_FILENAME
    manifest = json.loads(path.read_text())
    manifest["readiness"]["admit_006_unified_adapter_implemented"] = True
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(AssertionError):
        _load_checker()._validate_output_tree(candidate, expected_materialized=expected)


def test_production_and_checker_imports_are_silent() -> None:
    commands = [
        [sys.executable, "-c", f"import sys;sys.path.insert(0,{str(ROOT / 'src')!r});import {gate.__name__}"],
        [sys.executable, "-c", f"import importlib.util;s=importlib.util.spec_from_file_location('c',{str(CHECKER_PATH)!r});m=importlib.util.module_from_spec(s);s.loader.exec_module(m)"],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        assert result.returncode == 0 and result.stdout == result.stderr == ""


def test_checker_passes_and_reports_exact_counts() -> None:
    result = subprocess.run([sys.executable, str(CHECKER_PATH)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0 and result.stderr == ""
    payload = json.loads(result.stdout)
    assert (payload["source_count"], payload["routing_rows"], payload["truth_rows"], payload["issue_rows"]) == (13, 23, 56, 11)


def _copy_output_tree(destination: Path) -> None:
    shutil.copytree(OUTPUT_ROOT, destination)


def _rewrite_csv(path: Path, mutator) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None
        fieldnames, rows = list(reader.fieldnames), list(reader)
    mutator(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _refresh_manifest_output_sha(root: Path, filename: str) -> None:
    path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(path.read_text())
    manifest["output_sha256"][filename] = hashlib.sha256((root / filename).read_bytes()).hexdigest()
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def _semantic_csv_tamper(tmp_path: Path, filename: str, mutator) -> Path:
    candidate = tmp_path / "candidate"
    _copy_output_tree(candidate)
    _rewrite_csv(candidate / filename, mutator)
    _refresh_manifest_output_sha(candidate, filename)
    return candidate


@pytest.mark.parametrize(
    ("subject", "replacement", "delete"),
    [
        ("future_exact6_order", "ADMIT_001|ADMIT_002|ADMIT_003|ADMIT_004|ADMIT_006|ADMIT_005", False),
        ("complete_execution_precedence", "known_rule_validation|global_admission_rule_id_exact_type_validation", False),
        ("exact_builtin_empty_str", "", True),
        ("blocked", "rejected_passthrough", False),
        ("next_step", "implement_some_other_step", False),
    ],
)
def test_independent_exact43_rejects_self_consistent_tamper(
    tmp_path: Path, subject: str, replacement: str, delete: bool
) -> None:
    def mutate(rows: list[dict[str, str]]) -> None:
        index = next(i for i, row in enumerate(rows) if row["contract_subject"] == subject)
        if delete:
            rows.pop(index)
        else:
            rows[index]["contract_value"] = replacement

    candidate = _semantic_csv_tamper(tmp_path, gate.CONTRACT_FILENAME, mutate)
    with pytest.raises(AssertionError, match="Exact43 contract rows mismatch"):
        _load_checker()._validate_output_tree(candidate, enforce_frozen_hashes=False)


@pytest.mark.parametrize(
    "tamper_kind",
    [
        "formal_call_zero", "oracle_call_zero", "candidate_access", "consumed_context_empty",
        "missing_normalized", "routed_context_dispatch", "distance_missing", "adapter_ready_false",
    ],
)
def test_independent_exact23_rejects_semantic_tamper(tmp_path: Path, tamper_kind: str) -> None:
    def mutate(rows: list[dict[str, str]]) -> None:
        by_id = {row["case_id"]: row for row in rows}
        if tamper_kind == "formal_call_zero":
            by_id["evaluation_mapping_subclass"]["formal_call_count"] = "0"
        elif tamper_kind == "oracle_call_zero":
            by_id["scalar_identity"]["oracle_call_count"] = "0"
        elif tamper_kind == "candidate_access":
            by_id["batch_non_none"]["candidate_access_status"] = "accessed"
        elif tamper_kind == "consumed_context_empty":
            value = json.loads(by_id["candidate_non_mapping"]["expected_result_json"])
            value["consumed_context_items"] = []
            by_id["candidate_non_mapping"]["expected_result_json"] = json.dumps(value, separators=(",", ":"))
        elif tamper_kind == "missing_normalized":
            value = json.loads(by_id["candidate_exact_none"]["expected_result_json"])
            value["normalized_values"] = [["covalent_event_evidence_source", "distance_only_inference"]]
            by_id["candidate_exact_none"]["expected_result_json"] = json.dumps(value, separators=(",", ":"))
        elif tamper_kind == "routed_context_dispatch":
            by_id["invalid_value_reaches_standalone"]["expected_behavior"] = "dispatch_error"
        elif tamper_kind == "distance_missing":
            by_id["distance_not_missing"]["expected_reason"] = gate.MISSING_REASON
        else:
            value = json.loads(by_id["batch_non_none"]["expected_result_json"])
            value["adapter_ready"] = False
            by_id["batch_non_none"]["expected_result_json"] = json.dumps(value, separators=(",", ":"))

    candidate = _semantic_csv_tamper(tmp_path, gate.ROUTING_FILENAME, mutate)
    with pytest.raises(AssertionError, match="Exact23 routing rows mismatch"):
        _load_checker()._validate_output_tree(candidate, enforce_frozen_hashes=False)


@pytest.mark.parametrize(
    "tamper_kind",
    [
        "standalone_all_json", "blocked_rejected", "context_canonical_cleared",
        "source_invariant_oracle_called", "oracle_mismatch_not_called", "boundary_registered",
        "rows_reordered", "duplicate_case_id", "synchronized_case_passed_true",
    ],
)
def test_independent_exact56_rejects_synchronized_semantic_tamper(
    tmp_path: Path, tamper_kind: str
) -> None:
    def rewrite_json(row: dict[str, str], fields: tuple[str, ...], update) -> None:
        for field in fields:
            value = json.loads(row[field])
            update(value, field)
            row[field] = json.dumps(value, separators=(",", ":"))

    def mutate(rows: list[dict[str, str]]) -> None:
        by_id = {row["case_id"]: row for row in rows}
        if tamper_kind == "standalone_all_json":
            row = by_id["STANDALONE_CASE_001_canonical_structure_bond"]
            def update(value: dict[str, object], field: str) -> None:
                value["outcome"] = "rejected"
                value["passed"] = False
                value["blocks_candidate"] = True
            rewrite_json(row, ("source_exact10_json", "oracle_exact10_json", "unified_exact13_json"), update)
        elif tamper_kind == "blocked_rejected":
            row = by_id["PROJECTION_distance_blocked"]
            def update(value: dict[str, object], field: str) -> None:
                value["outcome"] = "rejected"
            rewrite_json(row, ("source_exact10_json", "oracle_exact10_json", "unified_exact13_json"), update)
        elif tamper_kind == "context_canonical_cleared":
            row = by_id["PROJECTION_context_invalid_canonical_retained"]
            def update(value: dict[str, object], field: str) -> None:
                if field != "unified_exact13_json":
                    value["canonical_covalent_event_evidence_source"] = ""
                value["validated_candidate_fields"] = []
                if field == "unified_exact13_json":
                    value["normalized_values"] = []
            rewrite_json(row, ("source_exact10_json", "oracle_exact10_json", "unified_exact13_json"), update)
        elif tamper_kind == "source_invariant_oracle_called":
            by_id["SOURCE_invariant"]["oracle_call_count"] = "1"
        elif tamper_kind == "oracle_mismatch_not_called":
            by_id["SOURCE_oracle_mismatch"]["oracle_call_count"] = "0"
        elif tamper_kind == "boundary_registered":
            by_id["BOUNDARY_admit006_not_registered"]["behavior"] = "registered"
        elif tamper_kind == "rows_reordered":
            rows[0], rows[1] = rows[1], rows[0]
        elif tamper_kind == "duplicate_case_id":
            rows[1]["case_id"] = rows[0]["case_id"]
        else:
            row = by_id["PROJECTION_explicit_passed"]
            row["expected_reason"] = "SYNCHRONIZED_WRONG_REASON"
            def update(value: dict[str, object], field: str) -> None:
                value["reason"] = "SYNCHRONIZED_WRONG_REASON"
            rewrite_json(row, ("source_exact10_json", "oracle_exact10_json", "unified_exact13_json"), update)
            assert row["case_passed"] == "true"

    candidate = _semantic_csv_tamper(tmp_path, gate.TRUTH_FILENAME, mutate)
    with pytest.raises(AssertionError, match="Exact56 truth rows mismatch"):
        _load_checker()._validate_output_tree(candidate, enforce_frozen_hashes=False)


@pytest.mark.parametrize(
    ("item", "value"),
    [
        ("adapter_handler_implementation", "true"),
        ("registry_modification", "true"),
        ("raw_read", "true"),
        ("training", "true"),
        ("fixed_ordered_source_boundary", "false"),
        ("__reorder__", ""),
    ],
)
def test_independent_exact41_rejects_safety_tamper(
    tmp_path: Path, item: str, value: str
) -> None:
    def mutate(rows: list[dict[str, str]]) -> None:
        if item == "__reorder__":
            rows[0], rows[1] = rows[1], rows[0]
            return
        row = next(row for row in rows if row["safety_item"] == item)
        row["expected_executed"] = value
        row["observed_executed"] = value

    candidate = _semantic_csv_tamper(tmp_path, gate.SAFETY_FILENAME, mutate)
    with pytest.raises(AssertionError, match="Exact41 safety rows mismatch"):
        _load_checker()._validate_output_tree(candidate, enforce_frozen_hashes=False)


@pytest.mark.parametrize("reference", ["gate._truth_rows()", "gate.SOURCE_PATHS"])
def test_ast_independence_guard_rejects_injected_production_reference(reference: str) -> None:
    checker = _load_checker()
    injected = f"def _expected_exact13():\n    return {reference}\n"
    with pytest.raises(AssertionError, match="depends on production"):
        checker._assert_ast_independence(injected)


def test_checker_owned_frozen_output_hash_map_is_exact() -> None:
    checker = _load_checker()
    assert checker.FROZEN_OUTPUT_SHA256 == {
        gate.CONTRACT_FILENAME: "2aee305dc9eece0631a3fe11791b78389639de8f1d573bee185a5046c95ae242",
        gate.ROUTING_FILENAME: "c43b1d1e071607a1040f5d66398164acad5eb01c6873aae32c95bf2796f08fab",
        gate.TRUTH_FILENAME: "c50fa504c6c569127e901f6256fd064b1dc7f773ea92c308279261dcfb9ae7c0",
        gate.SAFETY_FILENAME: "e34297ac8d8a8e8b841ed1e1ccd0d0783c3f5b755976cfa21a15af3f31797539",
        gate.ISSUE_FILENAME: "d3333fd74af79b065eb136d830e730c3a636e0d632bcb735b3e841a29d548c79",
        gate.MANIFEST_FILENAME: "449f3f2f5bcf7b7e6a2d60504238da91f41f67822a9747e32fd6eb60b88468b2",
    }


def test_frozen_hash_enforcement_rejects_before_manifest_trust(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    _copy_output_tree(candidate)
    path = candidate / gate.CONTRACT_FILENAME
    path.write_bytes(path.read_bytes() + b"tamper\n")
    _refresh_manifest_output_sha(candidate, gate.CONTRACT_FILENAME)
    with pytest.raises(AssertionError, match="frozen output SHA256 mismatch"):
        _load_checker()._validate_output_tree(candidate, enforce_frozen_hashes=True)


def test_checker_owned_source_boundary_matches_exact13() -> None:
    checker = _load_checker()
    assert len(checker.SOURCE_BOUNDARY) == 13
    assert tuple(path for path, _ in checker.SOURCE_BOUNDARY) == tuple(path.as_posix() for path in gate.SOURCE_PATHS)
    assert tuple(digest for _, digest in checker.SOURCE_BOUNDARY) == tuple(gate.SOURCE_SHA256[path] for path in gate.SOURCE_PATHS)
