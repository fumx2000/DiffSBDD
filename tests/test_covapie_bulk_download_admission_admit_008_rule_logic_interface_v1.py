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
import stat
import subprocess
import sys
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_admit_008_rule_logic_interface as subject,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate
    as committed_oracle,
)


CHECKER_PATH = subject.REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_008_rule_logic_interface_v1.py"
SPEC = importlib.util.spec_from_file_location("admit008_interface_checker", CHECKER_PATH)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


def _values(
    *, outcome: str = "passed", reason: str = "",
    canonical: str = "approved_restoration_template",
    validated: tuple[tuple[str, str], ...] | None = None,
) -> dict[str, object]:
    expected = () if canonical == "" else (("topology_restoration_disposition", canonical),)
    return {
        "admission_rule_id": "ADMIT_008", "outcome": outcome,
        "passed": outcome == "passed", "blocks_candidate": outcome != "passed",
        "reason": reason, "canonical_topology_restoration_disposition": canonical,
        "validated_candidate_fields": expected if validated is None else validated,
        "consumed_candidate_fields": subject.CANDIDATE_FIELDS,
        "consumed_context_items": subject.CONTEXT_ITEMS, "evaluator_io_used": False,
    }


def _invalid(values: dict[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        subject.Admit008EvaluationResult(**values)  # type: ignore[arg-type]


def test_exact_public_signature_and_exact10_frozen_fields() -> None:
    signature = inspect.signature(subject.evaluate_admit_008)
    parameters = tuple(signature.parameters.values())
    assert tuple(parameter.name for parameter in parameters) == (
        "topology_restoration_disposition", "allowed_topology_restoration_dispositions",
    )
    assert all(parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD for parameter in parameters)
    assert all(parameter.default is inspect.Parameter.empty for parameter in parameters)
    assert signature.return_annotation == "Admit008EvaluationResult"
    assert tuple(field.name for field in fields(subject.Admit008EvaluationResult)) == subject.RESULT_FIELDS
    result = subject.evaluate_admit_008(subject.CANONICAL_ENUM_MEMBERS[0], subject.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS)
    with pytest.raises(FrozenInstanceError):
        result.reason = "changed"  # type: ignore[misc]


def test_result_subclass_is_rejected() -> None:
    class ResultSubclass(subject.Admit008EvaluationResult):
        pass
    with pytest.raises(TypeError, match="subclasses"):
        ResultSubclass(**_values())  # type: ignore[arg-type]


@pytest.mark.parametrize("override", (
    {"admission_rule_id": "ADMIT_007"}, {"outcome": "rejected", "passed": False, "blocks_candidate": True, "reason": "x"},
    {"passed": False}, {"blocks_candidate": True}, {"reason": subject.BLOCKED_REASONS[subject.CANONICAL_ENUM_MEMBERS[2]]},
    {"validated_candidate_fields": ()}, {"consumed_candidate_fields": ()},
    {"consumed_context_items": ()}, {"evaluator_io_used": True},
))
def test_general_result_invariants_fail_closed(override: dict[str, object]) -> None:
    values = _values(); values.update(override); _invalid(values)


@pytest.mark.parametrize("values", (
    _values(outcome="passed", canonical="manual_review_required"),
    _values(outcome="passed", canonical="unknown"),
    _values(outcome="blocked", reason="TOPOLOGY_RESTORATION_MANUAL_REVIEW_REQUIRED"),
    _values(outcome="blocked", reason="TOPOLOGY_RESTORATION_QUARANTINE_REQUIRED", canonical="manual_review_required"),
    _values(outcome="blocked", reason="TOPOLOGY_RESTORATION_MANUAL_REVIEW_REQUIRED", canonical="quarantine_required"),
    _values(outcome="invalid", reason=subject.CONTEXT_REASONS[0], canonical=""),
    _values(outcome="invalid", reason=subject.SCALAR_REASONS[0], canonical="approved_restoration_template"),
    _values(outcome="invalid", reason=subject.CONTEXT_REASONS[1], validated=()),
    _values(outcome="invalid", reason="topology_restoration_unapproved", canonical=""),
    _values(outcome="blocked", reason="", canonical="manual_review_required"),
))
def test_semantic_result_conflicts_fail_closed(values: dict[str, object]) -> None:
    _invalid(values)


def test_result_exact_types_reject_str_tuple_pair_and_bool_subclasses() -> None:
    class Text(str): pass
    class TupleSubclass(tuple): pass
    class IntBool(int): pass
    values = _values(); values["admission_rule_id"] = Text("ADMIT_008"); _invalid(values)
    values = _values(); values["validated_candidate_fields"] = TupleSubclass(values["validated_candidate_fields"]); _invalid(values)
    values = _values(); values["validated_candidate_fields"] = ((Text("topology_restoration_disposition"), "approved_restoration_template"),); _invalid(values)
    values = _values(); values["validated_candidate_fields"] = (["topology_restoration_disposition", "approved_restoration_template"],); _invalid(values)
    values = _values(); values["consumed_context_items"] = TupleSubclass(subject.CONTEXT_ITEMS); _invalid(values)
    values = _values(); values["passed"] = IntBool(1); _invalid(values)


@pytest.mark.parametrize(("scalar", "reason"), (
    (None, subject.SCALAR_REASONS[0]), (7, subject.SCALAR_REASONS[0]),
    (True, subject.SCALAR_REASONS[0]), ("", subject.SCALAR_REASONS[1]),
    ("réview", subject.SCALAR_REASONS[2]), (" Approved", subject.SCALAR_REASONS[3]),
    ("approved-restoration-template", subject.SCALAR_REASONS[3]),
    ("unregistered_disposition", subject.SCALAR_REASONS[4]),
))
def test_scalar_validation_precedence_and_empty_canonical(scalar: object, reason: str) -> None:
    result = subject.evaluate_admit_008(scalar, None)
    assert result.outcome == "invalid" and result.reason == reason
    assert result.canonical_topology_restoration_disposition == ""
    assert result.validated_candidate_fields == ()


def test_exact_empty_differs_from_empty_str_subclass_and_no_normalization() -> None:
    class Text(str): pass
    assert subject.evaluate_admit_008("", subject.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS).reason == subject.SCALAR_REASONS[1]
    assert subject.evaluate_admit_008(Text(""), subject.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS).reason == subject.SCALAR_REASONS[0]
    for value in (" approved_restoration_template", "approved_restoration_template ", "Approved_restoration_template"):
        assert subject.evaluate_admit_008(value, subject.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS).reason == subject.SCALAR_REASONS[3]


@pytest.mark.parametrize("context", (None, list(subject.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS), set(subject.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS), frozenset(subject.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS)))
def test_context_non_tuple_uses_type_reason_and_retains_pair(context: object) -> None:
    scalar = subject.CANONICAL_ENUM_MEMBERS[0]
    result = subject.evaluate_admit_008(scalar, context)
    assert result.reason == subject.CONTEXT_REASONS[0]
    assert result.canonical_topology_restoration_disposition == scalar
    assert result.validated_candidate_fields == ((subject.CANDIDATE_FIELDS[0], scalar),)


@pytest.mark.parametrize("context", (
    tuple(reversed(subject.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS)),
    subject.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS[:1],
    (subject.CANONICAL_ENUM_MEMBERS[0], subject.CANONICAL_ENUM_MEMBERS[0]),
    (*subject.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS, subject.CANONICAL_ENUM_MEMBERS[2]),
    (*subject.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS, "unknown"),
    (*subject.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS, "extra"),
))
def test_context_wrong_content_order_duplicate_blocked_unknown_extra(context: object) -> None:
    result = subject.evaluate_admit_008(subject.CANONICAL_ENUM_MEMBERS[0], context)
    assert result.reason == subject.CONTEXT_REASONS[1]
    assert result.validated_candidate_fields


def test_context_tuple_subclass_and_str_subclass_member_are_rejected() -> None:
    class TupleSubclass(tuple): pass
    class Text(str): pass
    result = subject.evaluate_admit_008(subject.CANONICAL_ENUM_MEMBERS[0], TupleSubclass(subject.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS))
    assert result.reason == subject.CONTEXT_REASONS[0]
    result = subject.evaluate_admit_008(subject.CANONICAL_ENUM_MEMBERS[0], (Text(subject.CANONICAL_ENUM_MEMBERS[0]), subject.CANONICAL_ENUM_MEMBERS[1]))
    assert result.reason == subject.CONTEXT_REASONS[1]


def test_two_passed_and_two_distinct_blocked_outcomes_preserve_canonical() -> None:
    exact = subject.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS
    for scalar in exact:
        result = subject.evaluate_admit_008(scalar, exact)
        assert (result.outcome, result.passed, result.blocks_candidate, result.reason) == ("passed", True, False, "")
    reasons = []
    for scalar in subject.CANONICAL_ENUM_MEMBERS[2:]:
        result = subject.evaluate_admit_008(scalar, exact)
        assert result.outcome == "blocked" and result.blocks_candidate is True
        assert result.reason == subject.BLOCKED_REASONS[scalar]
        assert result.canonical_topology_restoration_disposition == scalar
        assert result.validated_candidate_fields == ((subject.CANDIDATE_FIELDS[0], scalar),)
        reasons.append(result.reason)
    assert len(set(reasons)) == 2
    assert "topology_restoration_unapproved" not in subject.REASON_VOCABULARY


def test_scalar_failure_precedes_and_short_circuits_context(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(_: object) -> str: raise AssertionError("context reached")
    monkeypatch.setattr(subject, "_validate_context", forbidden)
    result = subject.evaluate_admit_008("UNKNOWN", object())
    assert result.reason == subject.SCALAR_REASONS[3]


def test_evaluator_consumption_io_determinism_and_no_mutation() -> None:
    scalar = subject.CANONICAL_ENUM_MEMBERS[0]
    context = list(subject.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS)
    before = list(context)
    first = subject.evaluate_admit_008(scalar, context)
    second = subject.evaluate_admit_008(scalar, context)
    assert first == second and context == before
    assert first.consumed_candidate_fields == subject.CANDIDATE_FIELDS
    assert first.consumed_context_items == subject.CONTEXT_ITEMS
    assert first.evaluator_io_used is False


def test_exact38_matches_independent_expected_and_committed_oracle_complete_exact10() -> None:
    definitions = checker._definitions()
    assert len(definitions) == 38
    for _, _, scalar, _, context in definitions:
        observed = subject.evaluate_admit_008(scalar, context)
        expected = checker._checker_expected(scalar, context)
        oracle = committed_oracle.classify_admit_008_topology_restoration_disposition_design(scalar, context)
        oracle_full = (
            "ADMIT_008", oracle.admit_008.outcome, oracle.admit_008.passed,
            oracle.admit_008.blocks_candidate, oracle.admit_008.reason,
            oracle.admit_008.canonical_value, oracle.admit_008.validated_candidate_fields,
            subject.CANDIDATE_FIELDS, subject.CONTEXT_ITEMS, False,
        )
        assert tuple(getattr(observed, name) for name in subject.RESULT_FIELDS) == tuple(getattr(expected, name) for name in subject.RESULT_FIELDS) == oracle_full


def test_exact38_groups_and_materialized_complete_results() -> None:
    state = subject.build_interface_state()
    assert {group: sum(row["case_group"] == group for row in state["truth_rows"]) for group in checker.CHECKER_GROUPS} == checker.CHECKER_GROUPS
    assert len(state["truth_rows"]) == 38
    assert all(row["case_passed"] == row["production_oracle_equality"] == "true" for row in state["truth_rows"])
    assert all(row["expected_full_result"] == row["observed_full_result"] == row["committed_oracle_full_result"] for row in state["truth_rows"])


def test_public_evaluator_call_graph_is_exact_pure_and_oracle_not_imported() -> None:
    checker._check_call_graph()
    tree = ast.parse(Path(subject.__file__).read_text())
    imports = ast.dump(tree)
    assert "ImportFrom(module='covalent_ext" not in imports
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "evaluate_admit_008")
    assert "classify_admit_008_topology_restoration_disposition_design" not in ast.dump(function)


def test_production_does_not_consume_provider_or_adapter_fields() -> None:
    signature = inspect.signature(subject.evaluate_admit_008)
    forbidden = {"restoration_rule_id", "restoration_rule_scope", "restoration_rule_source", "candidate_record"}
    assert forbidden.isdisjoint(signature.parameters)
    source = Path(subject.__file__).read_text()
    evaluator = ast.get_source_segment(source, next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == "evaluate_admit_008"))
    assert evaluator is not None and forbidden.isdisjoint(set(evaluator.split()))


def test_exact11_source_structure_sha_and_non_descendant_guards(monkeypatch: pytest.MonkeyPatch) -> None:
    snapshot = subject.build_frozen_source_snapshot()
    assert subject.validate_frozen_source_snapshot(snapshot)
    assert len(snapshot.records) == 11 and tuple(subject.SOURCE_SHA256) == subject.SOURCE_PATHS
    assert subject._safe_relative_path(Path("../escape")) is False
    assert subject._safe_relative_path(Path("data/raw/forbidden.cif")) is False
    assert subject._safe_relative_path(Path("checkpoints/forbidden.ckpt")) is False
    original = subject._git
    def non_descendant(arguments: object, root: Path, *, text: bool = True) -> object:
        args = tuple(arguments)  # type: ignore[arg-type]
        if args[:2] == ("merge-base", "--is-ancestor"):
            return subprocess.CompletedProcess(args, 1, "" if text else b"", "" if text else b"")
        return original(arguments, root, text=text)  # type: ignore[arg-type]
    monkeypatch.setattr(subject, "_git", non_descendant)
    with pytest.raises(ValueError, match="not an ancestor"):
        subject.build_frozen_source_snapshot()


def test_all_source_structure_checks_precede_first_byte_read(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    structure = subject._structural_source_check
    git = subject._git
    def observed_structure(path: Path, root: Path) -> bool:
        events.append(f"s:{path}"); return structure(path, root)
    def observed_git(arguments: object, root: Path, *, text: bool = True) -> object:
        args = tuple(arguments)  # type: ignore[arg-type]
        if args[:1] == ("show",) and len(args) == 2: events.append("read")
        return git(arguments, root, text=text)  # type: ignore[arg-type]
    monkeypatch.setattr(subject, "_structural_source_check", observed_structure)
    monkeypatch.setattr(subject, "_git", observed_git)
    subject.build_frozen_source_snapshot()
    first = events.index("read")
    assert first == 11 and all(event.startswith("s:") for event in events[:first])


def test_issue_inventory_is_authoritative_exact11_byte_identical_and_coverage_unchanged() -> None:
    state = subject.build_interface_state()
    source = subject._record(state["source_snapshot"], subject.AUTHORITATIVE_ISSUE_PATH).content_bytes
    observed = subject._csv_bytes(subject.ISSUE_COLUMNS, state["issue_rows"])
    assert observed == source == state["issue_bytes"]
    assert hashlib.sha256(observed).hexdigest() == "229251600f0c6ae389633fff86af8859280b86664521ecce04c494906dc39695"
    issue_map = {row["issue_id"]: row for row in state["issue_rows"]}
    assert issue_map["TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED"]["status"] == "resolved"
    coverage = issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    assert coverage["status"] == "open" and coverage["affected_rules"].startswith("ADMIT_008|")


def test_checker_rejects_issue_coverage_and_semantic_tamper_with_hash_refresh(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    result = subject.run_covapie_bulk_download_admission_admit_008_rule_logic_interface_v1(root)
    expected, _ = subject._payloads(result["state"])
    checker._validate_output_tree(root, enforce_frozen_hashes=False)
    path = root / subject.TRUTH_FILENAME
    rows = list(csv.DictReader(io.StringIO(path.read_text(), newline="")))
    rows[0]["observed_full_result"] = rows[1]["observed_full_result"]
    stream = io.StringIO(newline=""); writer = csv.DictWriter(stream, fieldnames=subject.TRUTH_COLUMNS, lineterminator="\n")
    writer.writeheader(); writer.writerows(rows); path.write_text(stream.getvalue())
    manifest_path = root / subject.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text()); manifest["output_sha256"][subject.TRUTH_FILENAME] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(AssertionError): checker._validate_output_tree(root, enforce_frozen_hashes=False)
    assert expected[subject.TRUTH_FILENAME] != path.read_bytes()


def test_deterministic_materialization_exact_outputs_and_fail_closed_entries(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    first = subject.run_covapie_bulk_download_admission_admit_008_rule_logic_interface_v1(root)
    first_bytes = {name: (root / name).read_bytes() for name in subject.OUTPUT_FILES}
    second = subject.run_covapie_bulk_download_admission_admit_008_rule_logic_interface_v1(root)
    assert first["manifest"] == second["manifest"]
    assert first_bytes == {name: (root / name).read_bytes() for name in subject.OUTPUT_FILES}
    assert set(first_bytes) == set(subject.OUTPUT_FILES)
    assert all((root / name).is_file() and not (root / name).is_symlink() for name in subject.OUTPUT_FILES)
    extra = tmp_path / "extra"; shutil.copytree(root, extra); (extra / "unexpected.txt").write_text("x")
    with pytest.raises(ValueError): subject.run_covapie_bulk_download_admission_admit_008_rule_logic_interface_v1(extra)
    unsafe = tmp_path / "unsafe"; unsafe.mkdir(); outside = tmp_path / "outside"; outside.write_text("unchanged")
    (unsafe / subject.CONTRACT_FILENAME).symlink_to(outside)
    with pytest.raises(ValueError): subject.run_covapie_bulk_download_admission_admit_008_rule_logic_interface_v1(unsafe)
    assert outside.read_text() == "unchanged"


def test_manifest_readiness_provider_and_stop_boundaries_are_truthful() -> None:
    state = subject.build_interface_state()
    payloads, manifest = subject._payloads(state)
    assert set(manifest["readiness"]) == set(subject.READINESS)
    assert all(manifest[key] is manifest["readiness"][key] for key in subject.READINESS)
    assert manifest["real_provider_value_count"] == 0 and manifest["real_provider_mapping_executed"] is False
    assert manifest["admit_008_standalone_evaluator_implemented"] is True
    assert manifest["admit_008_unified_adapter_contract_frozen"] is False
    assert manifest["admit_008_registered_in_engine"] is False and manifest["exact7_runtime_modified"] is False
    assert manifest["admit_009_standalone_evaluator_implemented"] is False
    assert manifest["ready_for_bulk_download_now"] is manifest["ready_for_training"] is False
    assert subject.MANIFEST_FILENAME not in manifest["output_sha256"]
    assert len(payloads) == 6


def test_production_and_checker_imports_are_silent_without_materialization(tmp_path: Path) -> None:
    environment = dict(os.environ); environment["PYTHONPATH"] = str(subject.REPO_ROOT / "src")
    commands = (
        "import covalent_ext.covapie_bulk_download_admission_admit_008_rule_logic_interface",
        f"import importlib.util,sys;s=importlib.util.spec_from_file_location('check',{str(CHECKER_PATH)!r});m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)",
    )
    for command in commands:
        result = subprocess.run([sys.executable, "-c", command], cwd=tmp_path, env=environment, capture_output=True, text=True)
        assert result.returncode == 0 and result.stdout == result.stderr == ""
    assert tuple(tmp_path.iterdir()) == ()
