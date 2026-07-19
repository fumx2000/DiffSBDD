from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from dataclasses import fields
from pathlib import Path

import pytest

from covalent_ext import covapie_bulk_download_admission_admit_008_rule_logic_interface as standalone
from covalent_ext import covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate as oracle
from covalent_ext import covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate as gate


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CHECKER = importlib.import_module(
    "scripts.check_covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1"
)
OUTPUT_ROOT = ROOT / gate.DEFAULT_OUTPUT_ROOT


def _copy_outputs(destination: Path) -> None:
    destination.mkdir()
    for name in gate.OUTPUT_FILES:
        shutil.copy2(OUTPUT_ROOT / name, destination / name)


def _rewrite_csv(path: Path, mutate) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header, rows = list(reader.fieldnames or ()), list(reader)
    mutate(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _refresh_manifest_hash(root: Path, filename: str) -> None:
    path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["output_sha256"][filename] = hashlib.sha256((root / filename).read_bytes()).hexdigest()
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_identity_and_current_exact7_public_contract_are_frozen() -> None:
    runtime = importlib.import_module(
        "covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007"
    )
    assert gate.ADAPTER_ID == "covapie_admit_008_unified_adapter_v1"
    assert gate.RESULT_SCHEMA_VERSION == runtime.RESULT_SCHEMA_VERSION
    assert gate.RESULT_FIELDS == runtime.RESULT_FIELDS
    assert gate.DISPATCH_ERROR_FIELDS == runtime.DISPATCH_ERROR_FIELDS
    assert gate.CURRENT_REGISTERED_RULE_ORDER == tuple(runtime.EVALUATOR_REGISTRY)
    assert gate.FUTURE_REGISTERED_RULE_ORDER == (*gate.CURRENT_REGISTERED_RULE_ORDER, "ADMIT_008")


def test_source_boundary_exact17_is_committed_and_verified() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert len(snapshot.records) == 17
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert all(record.expected_sha256 == record.base_tree_sha256 == record.filesystem_sha256 for record in snapshot.records)


def test_source_boundary_rejects_unsafe_and_non_descendant_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    assert not gate._safe_path(Path("data/raw/example.csv"))
    assert not gate._safe_path(Path("checkpoints/model.ckpt"))
    assert not gate._safe_path(Path("../escape"))
    monkeypatch.setattr(gate, "EXPECTED_BASE_COMMIT", "0" * 40)
    with pytest.raises(ValueError, match="expected base unavailable"):
        gate.build_frozen_source_snapshot()


def test_predecessor_contracts_and_issue_bytes_fail_closed() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    predecessor = gate._validate_predecessors(snapshot)
    assert len(predecessor["truth_rows"]) == 38
    assert len(predecessor["issue_rows"]) == 11
    assert hashlib.sha256(predecessor["issue_bytes"]).hexdigest() == gate.SOURCE_SHA256[gate.SOURCE_PATHS[7]]


def test_source_validation_requires_exact_committed_type() -> None:
    source = standalone.evaluate_admit_008(gate.CANONICAL_ENUM_MEMBERS[0], gate.ALLOWED_DISPOSITIONS)
    assert gate.validate_source_shape_and_invariants_for_design(source).accepted
    for invalid in (source.__dict__.copy(), tuple(vars(source).values()), object()):
        decision = gate.validate_source_shape_and_invariants_for_design(invalid)
        assert not decision.accepted
        assert decision.reason == gate.SOURCE_TYPE_REASON
        assert decision.adapter_ready is False


def test_source_subclass_and_field_order_drift_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    class ResultSubclass(standalone.Admit008EvaluationResult):
        pass

    subclass = object.__new__(ResultSubclass)
    decision = gate.validate_source_shape_and_invariants_for_design(subclass)
    assert not decision.accepted and decision.reason == gate.SOURCE_TYPE_REASON
    source = standalone.evaluate_admit_008(gate.CANONICAL_ENUM_MEMBERS[0], gate.ALLOWED_DISPOSITIONS)
    original = gate.fields
    monkeypatch.setattr(gate, "fields", lambda value: tuple(reversed(original(value))))
    decision = gate.validate_source_shape_and_invariants_for_design(source)
    assert not decision.accepted and decision.reason == gate.SOURCE_INVARIANT_REASON


def test_oracle_receives_same_objects_exactly_once(monkeypatch: pytest.MonkeyPatch) -> None:
    scalar = gate._TruthStringSubclass("approved_restoration_template")
    context = ["approved_restoration_template", "explicit_manual_review_approved"]
    calls: list[tuple[object, object]] = []
    original = oracle.classify_admit_008_topology_restoration_disposition_design

    def wrapped(left: object, right: object):
        calls.append((left, right))
        return original(left, right)

    monkeypatch.setattr(oracle, "classify_admit_008_topology_restoration_disposition_design", wrapped)
    expected = gate.expected_exact10_from_committed_oracle_for_design(scalar, context)
    assert len(calls) == 1 and calls[0][0] is scalar and calls[0][1] is context
    assert expected.reason == gate.SCALAR_REASONS[0]


def test_formal_and_oracle_are_each_called_once_for_design_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    scalar = object()
    context = gate.ALLOWED_DISPOSITIONS
    formal_calls: list[tuple[object, object]] = []
    oracle_calls: list[tuple[object, object]] = []
    formal = standalone.evaluate_admit_008
    classify = oracle.classify_admit_008_topology_restoration_disposition_design

    def formal_wrapper(left: object, right: object):
        formal_calls.append((left, right))
        return formal(left, right)

    def oracle_wrapper(left: object, right: object):
        oracle_calls.append((left, right))
        return classify(left, right)

    monkeypatch.setattr(standalone, "evaluate_admit_008", formal_wrapper)
    monkeypatch.setattr(oracle, "classify_admit_008_topology_restoration_disposition_design", oracle_wrapper)
    gate._evaluate_pair_for_evidence(scalar, context)
    assert len(formal_calls) == len(oracle_calls) == 1
    assert formal_calls[0][0] is oracle_calls[0][0] is scalar
    assert formal_calls[0][1] is oracle_calls[0][1] is context


@pytest.mark.parametrize(
    ("scalar", "outcome", "reason", "validated"),
    (
        (None, "invalid", gate.SCALAR_REASONS[0], ()),
        ("", "invalid", gate.SCALAR_REASONS[1], ()),
        (gate._TruthStringSubclass(""), "invalid", gate.SCALAR_REASONS[0], ()),
        (" ", "invalid", gate.SCALAR_REASONS[3], ()),
        ("unknown", "invalid", gate.SCALAR_REASONS[4], ()),
        (gate.CANONICAL_ENUM_MEMBERS[0], "passed", "", ((gate.CANDIDATE_FIELDS[0], gate.CANONICAL_ENUM_MEMBERS[0]),)),
        (gate.CANONICAL_ENUM_MEMBERS[1], "passed", "", ((gate.CANDIDATE_FIELDS[0], gate.CANONICAL_ENUM_MEMBERS[1]),)),
        (gate.CANONICAL_ENUM_MEMBERS[2], "blocked", gate.BLOCKED_REASONS[gate.CANONICAL_ENUM_MEMBERS[2]], ((gate.CANDIDATE_FIELDS[0], gate.CANONICAL_ENUM_MEMBERS[2]),)),
        (gate.CANONICAL_ENUM_MEMBERS[3], "blocked", gate.BLOCKED_REASONS[gate.CANONICAL_ENUM_MEMBERS[3]], ((gate.CANDIDATE_FIELDS[0], gate.CANONICAL_ENUM_MEMBERS[3]),)),
    ),
)
def test_exact10_to_exact13_projection_preserves_standalone_semantics(
    scalar: object, outcome: str, reason: str, validated: tuple[tuple[str, str], ...]
) -> None:
    source = standalone.evaluate_admit_008(scalar, gate.ALLOWED_DISPOSITIONS)
    expected = gate.expected_exact10_from_committed_oracle_for_design(scalar, gate.ALLOWED_DISPOSITIONS)
    assert gate.validate_source_oracle_equivalence_for_design(source, expected).accepted
    result = gate.project_exact10_to_exact13_for_design(source)
    assert (result.outcome, result.reason) == (outcome, reason)
    assert result.normalized_values == result.validated_candidate_fields == validated
    assert result.adapter_id == gate.ADAPTER_ID


def test_context_invalid_retains_canonical_pair() -> None:
    source = standalone.evaluate_admit_008(gate.CANONICAL_ENUM_MEMBERS[0], list(gate.ALLOWED_DISPOSITIONS))
    result = gate.project_exact10_to_exact13_for_design(source)
    pair = ((gate.CANDIDATE_FIELDS[0], gate.CANONICAL_ENUM_MEMBERS[0]),)
    assert result.outcome == "invalid"
    assert result.reason == gate.CONTEXT_VALUE_REASONS[0]
    assert result.normalized_values == result.validated_candidate_fields == pair


def test_adapter_envelope_invalid_results_do_not_claim_evaluator_calls() -> None:
    for reason in (gate.CANDIDATE_MAPPING_REASON, gate.MISSING_REASON):
        result = gate.candidate_invalid_exact13_for_design(reason)
        assert result.outcome == "invalid" and result.blocks_candidate
        assert result.normalized_values == result.validated_candidate_fields == ()
        assert result.consumed_candidate_fields == gate.CANDIDATE_FIELDS
        assert result.consumed_context_items == gate.CONTEXT_ITEMS


def test_exact26_routing_contract_has_required_order_and_counts() -> None:
    rows = gate._routing_rows()
    assert len(rows) == 26
    assert Counter(row["matrix_group"] for row in rows) == {"context": 11, "candidate": 15}
    assert [int(row["matrix_order"]) for row in rows] == list(range(1, 27))
    assert all(row["case_passed"] == "true" for row in rows)
    by_id = {row["case_id"]: row for row in rows}
    assert by_id["candidate_key_absent"]["formal_call_count"] == "0"
    assert by_id["candidate_exact_none"]["expected_reason"] == gate.SCALAR_REASONS[0]
    assert by_id["candidate_exact_empty"]["expected_reason"] == gate.SCALAR_REASONS[1]


def test_truth_contract_safety_and_readiness_counts() -> None:
    state = gate.build_design_state()
    assert len(state["contract_rows"]) == 54
    assert len(state["truth_rows"]) == 52
    assert len(state["safety_rows"]) == 40
    assert Counter(row["case_group"] for row in state["truth_rows"]) == {
        "standalone_exact38": 38, "routing_dispatch": 6, "adapter_candidate_invalid": 2,
        "source_validation_failure": 4, "issue_coverage_boundary": 2,
    }
    assert all(gate.READINESS[key] for key in gate.TRUE_READINESS)
    assert not any(gate.READINESS[key] for key in gate.FALSE_READINESS)


def test_issue_inventory_is_byte_identical_and_coverage_unchanged() -> None:
    generated = OUTPUT_ROOT / gate.ISSUE_FILENAME
    predecessor = ROOT / gate.SOURCE_PATHS[7]
    assert generated.read_bytes() == predecessor.read_bytes()
    assert hashlib.sha256(generated.read_bytes()).hexdigest() == "229251600f0c6ae389633fff86af8859280b86664521ecce04c494906dc39695"
    with generated.open(newline="", encoding="utf-8") as handle:
        issues = {row["issue_id"]: row for row in csv.DictReader(handle)}
    assert issues["TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED"]["status"] == "resolved"
    assert issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"].split("|")[:8] == [f"ADMIT_{index:03d}" for index in range(8, 16)]


def test_design_module_contains_no_handler_registry_or_runtime_api() -> None:
    source = Path(gate.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert "_evaluate_registered_admit_008" not in functions
    assert "evaluate_admission_rule" not in functions
    assert not any(
        isinstance(node, (ast.Assign, ast.AnnAssign))
        and any(isinstance(target, ast.Name) and target.id == "EVALUATOR_REGISTRY"
                for target in (node.targets if isinstance(node, ast.Assign) else [node.target]))
        for node in tree.body
    )


def test_runtime_and_frozen_predecessors_remain_at_exact_sha() -> None:
    for relative, digest in CHECKER.SOURCE_BOUNDARY:
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest


def test_double_materialization_is_byte_identical(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    gate.run_covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1(first)
    gate.run_covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1(second)
    assert all((first / name).read_bytes() == (second / name).read_bytes() for name in gate.OUTPUT_FILES)


def test_output_root_rejects_extra_file_and_symlink(tmp_path: Path) -> None:
    extra = tmp_path / "extra"
    extra.mkdir()
    (extra / "unexpected").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected output"):
        gate.run_covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1(extra)
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="directory and non-symlink"):
        gate.run_covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1(link)


@pytest.mark.parametrize(
    ("filename", "mutate"),
    (
        (gate.CONTRACT_FILENAME, lambda rows: rows[0].__setitem__("contract_value", "ADMIT_999")),
        (gate.ROUTING_FILENAME, lambda rows: rows[0].__setitem__("expected_reason", "wrong")),
        (gate.TRUTH_FILENAME, lambda rows: rows[0].__setitem__("expected_reason", "wrong")),
        (gate.SAFETY_FILENAME, lambda rows: rows[0].__setitem__("observed_executed", "false")),
    ),
)
def test_checker_rejects_semantic_tamper_with_refreshed_manifest_hash(
    tmp_path: Path, filename: str, mutate
) -> None:
    root = tmp_path / "outputs"
    _copy_outputs(root)
    _rewrite_csv(root / filename, mutate)
    _refresh_manifest_hash(root, filename)
    with pytest.raises(AssertionError):
        CHECKER._validate_output_tree(root, enforce_frozen_hashes=False)


def test_checker_rejects_issue_transition_even_with_refreshed_hash(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    _copy_outputs(root)
    _rewrite_csv(root / gate.ISSUE_FILENAME, lambda rows: next(row for row in rows if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE").__setitem__("affected_rules", "ADMIT_009|ADMIT_010"))
    _refresh_manifest_hash(root, gate.ISSUE_FILENAME)
    with pytest.raises(AssertionError):
        CHECKER._validate_output_tree(root, enforce_frozen_hashes=False)


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("future_registered_rule_order", ["ADMIT_008"]),
        ("admit_001_to_007_handler_identity_unchanged", False),
        ("execution_precedence", ["wrong"]),
        ("adapter_missing_categories", ["required_key_absent", "exact_none"]),
        ("blocked_reason_mapping", {"manual_review_required": "wrong"}),
        ("provider_fields_consumed", ["restoration_rule"]),
        ("real_provider_mapping_executed", True),
        ("admit_008_registered_in_engine", True),
        ("exact7_runtime_modified", True),
        ("ready_for_training", True),
    ),
)
def test_checker_rejects_manifest_semantic_drift(tmp_path: Path, key: str, value: object) -> None:
    root = tmp_path / "outputs"
    _copy_outputs(root)
    path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest[key] = value
    if key in manifest.get("readiness", {}):
        manifest["readiness"][key] = value
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        CHECKER._validate_output_tree(root, enforce_frozen_hashes=False)


def test_checker_rejects_unknown_manifest_key(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    _copy_outputs(root)
    path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["unknown_contract_key"] = True
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="complete dictionary"):
        CHECKER._validate_output_tree(root, enforce_frozen_hashes=False)


def test_production_and_checker_imports_are_silent_and_side_effect_free() -> None:
    before = subprocess.run(["git", "status", "--short", "--untracked-files=all"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    code = (
        "import covalent_ext.covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate;"
        "import scripts.check_covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1"
    )
    completed = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env={**os.environ, "PYTHONPATH": f"{ROOT / 'src'}:{ROOT}"}, capture_output=True, text=True, check=True)
    after = subprocess.run(["git", "status", "--short", "--untracked-files=all"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    assert completed.stdout == completed.stderr == ""
    assert before == after


def test_checker_runs_cleanly_twice_with_identical_stdout() -> None:
    command = [sys.executable, str(ROOT / "scripts/check_covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1.py")]
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    first = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, check=True)
    second = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, check=True)
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout


def test_required_exact42_negative_contract_inventory_is_explicit() -> None:
    cases = (
        "public_exact13_identity_replaced", "future_registry_order_wrong", "prior_handler_identity_changed",
        "context_precedence_changed", "context_failure_accesses_candidate", "evaluation_nonmapping_accepted",
        "evaluation_key_absence_ignored", "context_value_copied", "context_value_multiple_lookup",
        "candidate_nonmapping_accepted", "candidate_key_absence_sent_to_standalone", "none_folded_to_missing",
        "empty_folded_to_missing", "scalar_normalized", "scalar_copied_or_multiple_lookup",
        "formal_call_count_wrong", "source_subclass_accepted", "source_field_order_drift",
        "source_invariant_conflict_accepted", "oracle_call_count_wrong", "oracle_object_identity_changed",
        "partial_exact10_comparison", "oracle_mismatch_projected", "normalized_not_validated_pair",
        "blocked_changed_to_other_outcome", "blocked_reasons_swapped", "context_canonical_pair_cleared",
        "scalar_invalid_canonical_fabricated", "historical_lowercase_reappears", "provider_fields_consumed",
        "provider_mapping_claimed_validated", "admit008_registered_early", "exact7_runtime_modified",
        "coverage_transition_early", "issue_bytes_changed", "source_boundary_unsafe",
        "raw_or_checkpoint_source", "output_tree_unsafe", "semantic_tamper_refreshed_hash",
        "readiness_mirror_drift", "unknown_manifest_key", "import_side_effect",
    )
    assert len(cases) == len(set(cases)) == 42
    evidence = json.dumps({
        "contract": gate._contract_rows(), "routing": gate._routing_rows(),
        "truth": gate.build_design_state()["truth_rows"], "safety": gate._safety_rows(),
        "readiness": gate.READINESS,
    }, sort_keys=True)
    required_anchors = (
        "current_exact7_identity", "future_exact8_order", "candidate_not_accessed",
        "single_getitem_original_identity", "required_key_absent", gate.SCALAR_REASONS[0],
        gate.SCALAR_REASONS[1], "complete_ordered_exact10_equality", "two_distinct_blocked_reasons",
        "canonical_and_validated_pair_retained", "restoration_rule_and_provenance_not_consumed",
        "current_exact7_unmodified_admit008_not_registered", "byte_identical", "raw_read",
        "checkpoint", "feature_semantics_audit_required_before_training",
    )
    assert all(anchor in evidence for anchor in required_anchors)
