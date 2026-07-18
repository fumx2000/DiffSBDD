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
    covapie_bulk_download_admission_admit_007_rule_logic_interface as subject,
)
from covalent_ext import (
    covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate
    as committed_oracle,
)


CHECKER_PATH = (
    subject.REPO_ROOT
    / "scripts/check_covapie_bulk_download_admission_admit_007_rule_logic_interface_v1.py"
)
CHECKER_SPEC = importlib.util.spec_from_file_location("admit007_hardening_checker", CHECKER_PATH)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
sys.modules[CHECKER_SPEC.name] = checker
CHECKER_SPEC.loader.exec_module(checker)


def _result_values(
    *,
    outcome: str = "passed",
    reason: str = "",
    canonical: str = "explicit_structure_bond_record",
    validated: tuple[tuple[str, str], ...] | None = None,
) -> dict[str, object]:
    expected_validated = (
        ()
        if canonical == ""
        else (("covalent_event_evidence_source", canonical),)
    )
    return {
        "admission_rule_id": "ADMIT_007",
        "outcome": outcome,
        "passed": outcome == "passed",
        "blocks_candidate": outcome != "passed",
        "reason": reason,
        "canonical_covalent_event_evidence_source": canonical,
        "validated_candidate_fields": expected_validated if validated is None else validated,
        "consumed_candidate_fields": subject.CANDIDATE_FIELDS,
        "consumed_context_items": subject.CONTEXT_ITEMS,
        "evaluator_io_used": False,
    }


def _assert_invalid_construction(values: dict[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        subject.Admit007EvaluationResult(**values)  # type: ignore[arg-type]


def _independent_oracle(scalar: object, context: object) -> tuple[object, ...]:
    if type(scalar) is not str:
        outcome, reason, canonical = "invalid", subject.SCALAR_REASONS[0], ""
    elif scalar == "":
        outcome, reason, canonical = "invalid", subject.SCALAR_REASONS[1], ""
    elif any(ord(character) > 127 for character in scalar):
        outcome, reason, canonical = "invalid", subject.SCALAR_REASONS[2], ""
    elif __import__("re").fullmatch(r"[a-z][a-z0-9_]{0,63}", scalar, flags=__import__("re").ASCII) is None:
        outcome, reason, canonical = "invalid", subject.SCALAR_REASONS[3], ""
    elif scalar not in (
        "explicit_structure_bond_record",
        "explicit_curated_covalent_annotation",
        "distance_only_inference",
    ):
        outcome, reason, canonical = "invalid", subject.SCALAR_REASONS[4], ""
    else:
        canonical = scalar
        if type(context) is not tuple:
            outcome, reason = "invalid", subject.CONTEXT_REASONS[0]
        elif (
            len(context) != 2
            or type(context[0]) is not str
            or type(context[1]) is not str
            or context[0] != "explicit_structure_bond_record"
            or context[1] != "explicit_curated_covalent_annotation"
        ):
            outcome, reason = "invalid", subject.CONTEXT_REASONS[1]
        elif scalar == "distance_only_inference":
            outcome, reason = "blocked", subject.BLOCKED_REASON
        else:
            outcome, reason = "passed", ""
    validated = () if canonical == "" else ((subject.CANDIDATE_FIELDS[0], canonical),)
    return (
        "ADMIT_007",
        outcome,
        outcome == "passed",
        outcome != "passed",
        reason,
        canonical,
        validated,
        subject.CANDIDATE_FIELDS,
        subject.CONTEXT_ITEMS,
        False,
    )


def test_public_signature_is_exact_and_both_parameters_are_required() -> None:
    signature = inspect.signature(subject.evaluate_admit_007)
    parameters = tuple(signature.parameters.values())
    assert tuple(parameter.name for parameter in parameters) == (
        "covalent_event_evidence_source",
        "allowed_covalent_evidence_classes",
    )
    assert all(parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD for parameter in parameters)
    assert all(parameter.default is inspect.Parameter.empty for parameter in parameters)
    assert signature.return_annotation == "Admit007EvaluationResult"


def test_frozen_result_has_exact10_ordered_fields() -> None:
    assert tuple(field.name for field in fields(subject.Admit007EvaluationResult)) == subject.RESULT_FIELDS
    result = subject.evaluate_admit_007(
        subject.CANONICAL_ENUM_MEMBERS[0], subject.ALLOWED_COVALENT_EVIDENCE_CLASSES
    )
    with pytest.raises(FrozenInstanceError):
        result.reason = "changed"  # type: ignore[misc]


def test_result_subclass_is_rejected() -> None:
    class ResultSubclass(subject.Admit007EvaluationResult):
        pass

    with pytest.raises(TypeError, match="subclasses"):
        ResultSubclass(**_result_values())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "override",
    (
        {"admission_rule_id": "ADMIT_006"},
        {"outcome": "rejected", "passed": False, "blocks_candidate": True, "reason": "x"},
        {"passed": False},
        {"blocks_candidate": True},
        {"reason": subject.BLOCKED_REASON},
        {"consumed_candidate_fields": ()},
        {"consumed_context_items": ()},
        {"evaluator_io_used": True},
        {"validated_candidate_fields": ()},
    ),
)
def test_direct_construction_rejects_general_invariant_violations(override: dict[str, object]) -> None:
    values = _result_values()
    values.update(override)
    _assert_invalid_construction(values)


@pytest.mark.parametrize(
    "values",
    (
        _result_values(outcome="passed", canonical="distance_only_inference"),
        _result_values(outcome="passed", canonical="unknown"),
        _result_values(outcome="blocked", reason=subject.BLOCKED_REASON),
        _result_values(
            outcome="blocked", reason=subject.BLOCKED_REASON,
            canonical="explicit_curated_covalent_annotation",
        ),
        _result_values(
            outcome="invalid", reason=subject.CONTEXT_REASONS[0], canonical="",
        ),
        _result_values(
            outcome="invalid", reason=subject.SCALAR_REASONS[0],
            canonical="explicit_structure_bond_record",
        ),
        _result_values(
            outcome="invalid", reason=subject.CONTEXT_REASONS[1],
            canonical="explicit_structure_bond_record", validated=(),
        ),
        _result_values(
            outcome="invalid", reason=subject.SCALAR_REASONS[4], canonical="",
            validated=(("covalent_event_evidence_source", "unknown"),),
        ),
        _result_values(outcome="invalid", reason="", canonical=""),
        _result_values(outcome="blocked", reason="", canonical="distance_only_inference"),
    ),
)
def test_direct_construction_rejects_semantic_state_conflicts(values: dict[str, object]) -> None:
    _assert_invalid_construction(values)


def test_direct_construction_rejects_exact_str_and_tuple_subclasses() -> None:
    class Text(str):
        pass

    class TupleSubclass(tuple):
        pass

    values = _result_values()
    values["admission_rule_id"] = Text("ADMIT_007")
    _assert_invalid_construction(values)
    values = _result_values()
    values["validated_candidate_fields"] = TupleSubclass(values["validated_candidate_fields"])
    _assert_invalid_construction(values)
    values = _result_values()
    values["consumed_context_items"] = TupleSubclass(subject.CONTEXT_ITEMS)
    _assert_invalid_construction(values)


@pytest.mark.parametrize(
    ("scalar", "reason"),
    (
        (None, subject.SCALAR_REASONS[0]),
        (7, subject.SCALAR_REASONS[0]),
        (True, subject.SCALAR_REASONS[0]),
        ("", subject.SCALAR_REASONS[1]),
        ("é", subject.SCALAR_REASONS[2]),
        (" Explicit", subject.SCALAR_REASONS[3]),
        ("unregistered_value", subject.SCALAR_REASONS[4]),
    ),
)
def test_scalar_validation_precedence(scalar: object, reason: str) -> None:
    result = subject.evaluate_admit_007(scalar, None)
    assert result.outcome == "invalid"
    assert result.reason == reason
    assert result.canonical_covalent_event_evidence_source == ""
    assert result.validated_candidate_fields == ()


def test_scalar_exact_str_subclass_is_rejected_without_normalization() -> None:
    class Text(str):
        pass

    result = subject.evaluate_admit_007(
        Text(subject.CANONICAL_ENUM_MEMBERS[0]), subject.ALLOWED_COVALENT_EVIDENCE_CLASSES
    )
    assert result.reason == subject.SCALAR_REASONS[0]

    empty_result = subject.evaluate_admit_007(
        Text(""), subject.ALLOWED_COVALENT_EVIDENCE_CLASSES
    )
    assert empty_result.reason == subject.SCALAR_REASONS[0]
    assert subject.evaluate_admit_007(
        "", subject.ALLOWED_COVALENT_EVIDENCE_CLASSES
    ).reason == subject.SCALAR_REASONS[1]


@pytest.mark.parametrize(
    "context",
    (
        None,
        list(subject.ALLOWED_COVALENT_EVIDENCE_CLASSES),
        set(subject.ALLOWED_COVALENT_EVIDENCE_CLASSES),
        frozenset(subject.ALLOWED_COVALENT_EVIDENCE_CLASSES),
    ),
)
def test_wrong_context_container_has_type_reason(context: object) -> None:
    result = subject.evaluate_admit_007(subject.CANONICAL_ENUM_MEMBERS[0], context)
    assert result.reason == subject.CONTEXT_REASONS[0]
    assert result.canonical_covalent_event_evidence_source == subject.CANONICAL_ENUM_MEMBERS[0]


@pytest.mark.parametrize(
    "context",
    (
        tuple(reversed(subject.ALLOWED_COVALENT_EVIDENCE_CLASSES)),
        subject.ALLOWED_COVALENT_EVIDENCE_CLASSES[:1],
        (subject.CANONICAL_ENUM_MEMBERS[0], subject.CANONICAL_ENUM_MEMBERS[0]),
        (*subject.ALLOWED_COVALENT_EVIDENCE_CLASSES, subject.CANONICAL_ENUM_MEMBERS[2]),
        (*subject.ALLOWED_COVALENT_EVIDENCE_CLASSES, "unknown"),
        (*subject.ALLOWED_COVALENT_EVIDENCE_CLASSES, "explicit_database_bond"),
    ),
)
def test_wrong_context_content_has_content_reason(context: object) -> None:
    result = subject.evaluate_admit_007(subject.CANONICAL_ENUM_MEMBERS[0], context)
    assert result.reason == subject.CONTEXT_REASONS[1]
    assert result.validated_candidate_fields == ((
        subject.CANDIDATE_FIELDS[0], subject.CANONICAL_ENUM_MEMBERS[0]
    ),)


def test_context_exact_str_subclass_member_is_rejected() -> None:
    class Text(str):
        pass

    context = (Text(subject.CANONICAL_ENUM_MEMBERS[0]), subject.CANONICAL_ENUM_MEMBERS[1])
    result = subject.evaluate_admit_007(subject.CANONICAL_ENUM_MEMBERS[0], context)
    assert result.reason == subject.CONTEXT_REASONS[1]


def test_context_tuple_subclass_is_rejected() -> None:
    class TupleSubclass(tuple):
        pass

    context = TupleSubclass(subject.ALLOWED_COVALENT_EVIDENCE_CLASSES)
    result = subject.evaluate_admit_007(subject.CANONICAL_ENUM_MEMBERS[0], context)
    assert result.reason == subject.CONTEXT_REASONS[0]


@pytest.mark.parametrize("scalar", subject.ALLOWED_COVALENT_EVIDENCE_CLASSES)
def test_both_explicit_members_pass_with_empty_reason(scalar: str) -> None:
    result = subject.evaluate_admit_007(scalar, subject.ALLOWED_COVALENT_EVIDENCE_CLASSES)
    assert result.outcome == "passed"
    assert result.reason == ""
    assert result.passed is True and result.blocks_candidate is False


def test_distance_only_is_blocked_and_never_passed() -> None:
    result = subject.evaluate_admit_007(
        subject.CANONICAL_ENUM_MEMBERS[2], subject.ALLOWED_COVALENT_EVIDENCE_CLASSES
    )
    assert result.outcome == "blocked"
    assert result.reason == subject.BLOCKED_REASON
    assert result.reason != "COVALENT_EVENT_EVIDENCE_NOT_EXPLICIT"
    assert result.reason != "distance_only_inference_not_admissible"
    assert "COVALENT_EVENT_EVIDENCE_NOT_EXPLICIT" not in subject.REASON_VOCABULARY
    assert "distance_only_inference_not_admissible" not in subject.REASON_VOCABULARY
    assert result.canonical_covalent_event_evidence_source == subject.CANONICAL_ENUM_MEMBERS[2]


@pytest.mark.parametrize(
    "scalar",
    (None, "", "BAD", "unknown", "distance_only_inference"),
)
def test_standalone_never_uses_reserved_missing_reason(scalar: object) -> None:
    result = subject.evaluate_admit_007(scalar, subject.ALLOWED_COVALENT_EVIDENCE_CLASSES)
    assert result.reason != "covalent_event_evidence_missing"


def test_scalar_failure_wins_when_scalar_and_context_are_both_invalid() -> None:
    result = subject.evaluate_admit_007("UNKNOWN", None)
    assert result.reason == subject.SCALAR_REASONS[3]
    assert result.canonical_covalent_event_evidence_source == ""


def test_scalar_failure_does_not_semantically_access_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(_: object) -> str:
        raise AssertionError("context validation must be short-circuited")

    monkeypatch.setattr(subject, "_validate_context", forbidden)
    result = subject.evaluate_admit_007(None, object())
    assert result.reason == subject.SCALAR_REASONS[0]


def test_evaluator_is_deterministic_and_does_not_mutate_inputs() -> None:
    scalar = subject.CANONICAL_ENUM_MEMBERS[0]
    context = list(subject.ALLOWED_COVALENT_EVIDENCE_CLASSES)
    before = list(context)
    first = subject.evaluate_admit_007(scalar, context)
    second = subject.evaluate_admit_007(scalar, context)
    assert first == second
    assert context == before


def test_all_exact37_cases_match_a_separate_test_oracle() -> None:
    definitions = subject._truth_definitions()
    assert len(definitions) == 37
    for _, _, scalar, _, context in definitions:
        observed = subject.evaluate_admit_007(scalar, context)
        expected = _independent_oracle(scalar, context)
        assert tuple(getattr(observed, field.name) for field in fields(observed)) == expected
        design = committed_oracle.classify_admit_006_admit_007_evidence_design(
            scalar, context
        )
        canonical = (
            design.scalar.canonical_value
            if design.scalar.classification == "canonical"
            else ""
        )
        validated = () if canonical == "" else ((subject.CANDIDATE_FIELDS[0], canonical),)
        oracle_full = (
            "ADMIT_007", design.admit_007.outcome, design.admit_007.passed,
            design.admit_007.blocks_candidate, design.admit_007.reason, canonical,
            validated, subject.CANDIDATE_FIELDS, subject.CONTEXT_ITEMS, False,
        )
        assert oracle_full == expected


def test_exact37_group_counts_and_materialized_results() -> None:
    state = subject.build_interface_state()
    assert {group: sum(row["case_group"] == group for row in state["truth_rows"]) for group in (
        "canonical", "scalar_type", "empty_syntax", "unknown", "context"
    )} == {"canonical": 3, "scalar_type": 6, "empty_syntax": 11, "unknown": 5, "context": 12}
    assert all(row["case_passed"] == "true" for row in state["truth_rows"])


def test_source_boundary_row5_uses_preservation_wording_and_outputs_have_no_stale_claim(
    tmp_path: Path,
) -> None:
    expected = "ordered Exact11 issue inventory preservation baseline"
    stale = "one-row coverage transition"
    state = subject.build_interface_state()
    assert state["source_audit_rows"][8]["boundary_necessity"] == expected
    root = tmp_path / "outputs"
    subject.run_covapie_bulk_download_admission_admit_007_rule_logic_interface_v1(root)
    paths = tuple(root / name for name in subject.OUTPUT_FILES) + (
        subject.REPO_ROOT
        / "docs/covapie_bulk_download_admission_admit_007_rule_logic_interface_v1_summary.md",
    )
    assert all(stale not in path.read_text() for path in paths)


def _called_names(node: ast.AST) -> set[str]:
    values = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                values.add(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                values.add(child.func.attr)
    return values


def _assert_pure_call_graph(tree: ast.Module, root: str) -> set[str]:
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    pending = [root]
    closure: set[str] = set()
    banned = {
        "classify_admit_006_admit_007_evidence_design", "build_interface_state",
        "run_covapie_bulk_download_admission_admit_007_rule_logic_interface_v1",
        "build_frozen_source_snapshot", "_git", "open", "read", "read_bytes", "read_text",
        "write", "write_bytes", "write_text", "run", "Popen", "system", "urlopen", "request",
    }
    while pending:
        name = pending.pop()
        if name in closure:
            continue
        closure.add(name)
        calls = _called_names(functions[name])
        assert not calls.intersection(banned)
        pending.extend(call for call in calls if call in functions)
    return closure


def test_evaluator_transitive_call_graph_is_pure_and_oracle_independent() -> None:
    path = Path(subject.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    closure = _assert_pure_call_graph(tree, "evaluate_admit_007")
    assert closure == {"evaluate_admit_007", "_validate_scalar", "_validate_context", "_result"}


@pytest.mark.parametrize(
    "bad_call",
    (
        "classify_admit_006_admit_007_evidence_design(x)",
        "read_bytes(x)",
        "build_interface_state()",
    ),
)
def test_call_graph_guard_rejects_design_oracle_io_and_materializer_helpers(bad_call: str) -> None:
    tree = ast.parse(f"def evaluate_admit_007(x):\n    return helper(x)\ndef helper(x):\n    return {bad_call}\n")
    with pytest.raises(AssertionError):
        _assert_pure_call_graph(tree, "evaluate_admit_007")


def test_all_source_structure_checks_precede_first_source_byte_read(monkeypatch: pytest.MonkeyPatch) -> None:
    original = subject._git
    structural = 0
    first_read_after = -1

    def observed(arguments: object, repo_root: Path, *, text: bool = True) -> object:
        nonlocal structural, first_read_after
        args = tuple(arguments)  # type: ignore[arg-type]
        if args[:2] == ("ls-files", "--error-unmatch"):
            structural += 1
        if args[0] == "show" and len(args) == 2 and ":" in args[1] and first_read_after == -1:
            first_read_after = structural
        return original(arguments, repo_root, text=text)  # type: ignore[arg-type]

    monkeypatch.setattr(subject, "_git", observed)
    snapshot = subject.build_frozen_source_snapshot()
    assert subject.validate_frozen_source_snapshot(snapshot)
    assert structural == first_read_after == len(subject.SOURCE_PATHS)


def test_source_sha_mismatch_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = Path.read_bytes
    target = subject.REPO_ROOT / subject.SOURCE_PATHS[0]

    def tampered(path: Path) -> bytes:
        content = original(path)
        return content + b"tamper" if path == target else content

    monkeypatch.setattr(Path, "read_bytes", tampered)
    with pytest.raises(ValueError, match="source SHA256 mismatch"):
        subject.build_frozen_source_snapshot()


def test_source_symlink_metadata_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = subject.os.lstat
    target = subject.REPO_ROOT / subject.SOURCE_PATHS[0]

    def symlink_metadata(path: Path) -> object:
        if Path(path) == target:
            return os.stat_result((stat.S_IFLNK | 0o777, 0, 0, 0, 0, 0, 0, 0, 0, 0))
        return original(path)

    monkeypatch.setattr(subject.os, "lstat", symlink_metadata)
    assert subject._structural_source_check(subject.SOURCE_PATHS[0], subject.REPO_ROOT) is False


def test_non_descendant_base_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = subject._git

    def non_descendant(arguments: object, repo_root: Path, *, text: bool = True) -> object:
        args = tuple(arguments)  # type: ignore[arg-type]
        if args[:2] == ("merge-base", "--is-ancestor"):
            empty = "" if text else b""
            return subprocess.CompletedProcess(args, 1, empty, empty)
        return original(arguments, repo_root, text=text)  # type: ignore[arg-type]

    monkeypatch.setattr(subject, "_git", non_descendant)
    with pytest.raises(ValueError, match="not an ancestor"):
        subject.build_frozen_source_snapshot()


def test_issue_inventory_exactly_preserves_predecessor_exact11() -> None:
    snapshot = subject.build_frozen_source_snapshot()
    historical = subject._validate_predecessors(snapshot)
    state = subject.build_interface_state(snapshot)
    before = {row["issue_id"]: row for row in historical["issue_rows"]}
    after = {row["issue_id"]: row for row in state["issue_rows"]}
    assert tuple(before) == tuple(after) and len(after) == 11
    assert state["issue_rows"] == [dict(row) for row in historical["issue_rows"]]
    assert after["COVALENT_EVIDENCE_ENUM_UNRESOLVED"] == before["COVALENT_EVIDENCE_ENUM_UNRESOLVED"]
    coverage = after["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    assert coverage["status"] == "open"
    assert coverage["blocking_scope"] == "unified_admission_engine"
    assert coverage["affected_rules"] == "|".join(f"ADMIT_{index:03d}" for index in range(7, 16))
    assert coverage["integration_transition"] == "admit_006_implemented_and_removed_from_open_coverage_scope"
    assert after == before


def _committed_predecessor_truth_rows() -> tuple[dict[str, str], ...]:
    snapshot = subject.build_frozen_source_snapshot()
    return tuple(dict(row) for row in subject._validate_predecessors(snapshot)["truth_rows"])


def _disk_truth_rows() -> tuple[dict[str, str], ...]:
    path = subject.REPO_ROOT / subject.DEFAULT_OUTPUT_ROOT / subject.TRUTH_FILENAME
    return tuple(dict(row) for row in csv.DictReader(io.StringIO(path.read_text(), newline="")))


def test_checker_performs_full_four_way_exact37_verification() -> None:
    checker._verify_exact37_views(_committed_predecessor_truth_rows(), _disk_truth_rows())


def test_checker_rejects_changed_case_id() -> None:
    rows = [dict(row) for row in checker._checker_expected_disk_rows()]
    rows[0]["case_id"] = "CASE_001_renamed"
    with pytest.raises(AssertionError):
        checker._verify_exact37_views(_committed_predecessor_truth_rows(), tuple(rows))


def test_checker_rejects_reordered_exact37_rows() -> None:
    rows = list(checker._checker_expected_disk_rows())
    rows[0], rows[1] = rows[1], rows[0]
    with pytest.raises(AssertionError):
        checker._verify_exact37_views(_committed_predecessor_truth_rows(), tuple(rows))


def test_checker_rejects_same_semantics_type_none_input_substitution() -> None:
    rows = [dict(row) for row in checker._checker_expected_disk_rows()]
    rows[3]["scalar_input_kind"] = "int"
    rows[3]["scalar_input_display"] = "int:7"
    assert rows[3]["expected_outcome"] == rows[4]["expected_outcome"]
    assert rows[3]["expected_reason"] == rows[4]["expected_reason"]
    with pytest.raises(AssertionError):
        checker._verify_exact37_views(_committed_predecessor_truth_rows(), tuple(rows))


def test_checker_rejects_same_semantics_context_kind_display_substitution() -> None:
    rows = [dict(row) for row in checker._checker_expected_disk_rows()]
    rows[26]["context_input_kind"] = "list"
    rows[26]["context_input_display"] = checker._checker_display(
        list(checker.CHECKER_ALLOWED_CONTEXT)
    )
    assert rows[26]["expected_reason"] == rows[27]["expected_reason"]
    with pytest.raises(AssertionError):
        checker._verify_exact37_views(_committed_predecessor_truth_rows(), tuple(rows))


def test_checker_rejects_expected_and_observed_reason_changed_together() -> None:
    rows = [dict(row) for row in checker._checker_expected_disk_rows()]
    rows[20]["expected_reason"] = checker.CHECKER_SCALAR_REASONS[0]
    rows[20]["observed_reason"] = checker.CHECKER_SCALAR_REASONS[0]
    with pytest.raises(AssertionError):
        checker._verify_exact37_views(_committed_predecessor_truth_rows(), tuple(rows))


@pytest.mark.parametrize(
    "mutation",
    ("case_id", "reorder", "type_none", "context_display", "both_reasons"),
)
def test_checker_rejects_exact37_semantic_tamper_after_manifest_hash_refresh(
    tmp_path: Path,
    mutation: str,
) -> None:
    root = tmp_path / "outputs"
    materialized = subject.run_covapie_bulk_download_admission_admit_007_rule_logic_interface_v1(root)
    expected_payloads, _ = subject._payloads(materialized["state"])
    truth_path = root / subject.TRUTH_FILENAME
    rows = list(csv.DictReader(io.StringIO(truth_path.read_text(), newline="")))
    if mutation == "case_id":
        rows[0]["case_id"] = "CASE_001_renamed"
    elif mutation == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "type_none":
        rows[3]["scalar_input_kind"] = "int"
        rows[3]["scalar_input_display"] = "int:7"
    elif mutation == "context_display":
        rows[26]["context_input_kind"] = "list"
        rows[26]["context_input_display"] = checker._checker_display(
            list(checker.CHECKER_ALLOWED_CONTEXT)
        )
    else:
        rows[20]["expected_reason"] = checker.CHECKER_SCALAR_REASONS[0]
        rows[20]["observed_reason"] = checker.CHECKER_SCALAR_REASONS[0]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=subject.TRUTH_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    truth_path.write_text(stream.getvalue())
    manifest_path = root / subject.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text())
    refreshed_hash = hashlib.sha256(truth_path.read_bytes()).hexdigest()
    manifest["output_sha256"][subject.TRUTH_FILENAME] = refreshed_hash
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    assert json.loads(manifest_path.read_text())["output_sha256"][subject.TRUTH_FILENAME] == refreshed_hash
    with pytest.raises(AssertionError):
        checker._verify_exact37_views(
            _committed_predecessor_truth_rows(), tuple(dict(row) for row in rows)
        )
    with pytest.raises(AssertionError):
        checker._validate_output_tree(root, expected_payloads)


def test_production_truth_definition_drift_fails_against_ordered_predecessor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = subject.build_frozen_source_snapshot()
    original = subject._truth_definitions()
    checker_rows = checker._checker_expected_disk_rows()
    monkeypatch.setattr(subject, "_truth_definitions", lambda: tuple(reversed(original)))
    with pytest.raises(ValueError, match="ordered predecessor truth mismatch"):
        subject.build_interface_state(snapshot)
    assert checker._checker_expected_disk_rows() == checker_rows


@pytest.mark.parametrize(
    ("constant_name", "replacement"),
    (
        (
            "CANONICAL_ENUM_MEMBERS",
            ("drift_structure", "drift_curated", "drift_distance"),
        ),
        (
            "SCALAR_REASONS",
            (
                "DRIFT_TYPE", "DRIFT_EMPTY", "DRIFT_ASCII", "DRIFT_SYNTAX", "DRIFT_UNKNOWN",
            ),
        ),
    ),
)
def test_checker_expected_rows_ignore_production_enum_and_reason_constant_drift(
    monkeypatch: pytest.MonkeyPatch,
    constant_name: str,
    replacement: tuple[str, ...],
) -> None:
    expected_rows = checker._checker_expected_disk_rows()
    monkeypatch.setattr(subject, constant_name, replacement)
    assert checker._checker_expected_disk_rows() == expected_rows
    with pytest.raises((AssertionError, ValueError)):
        checker._verify_exact37_views(
            _committed_predecessor_truth_rows(), checker._checker_expected_disk_rows()
        )


def test_checker_independent_builder_ignores_production_truth_builder_monkeypatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before_definitions = checker._checker_truth_definitions()
    before_rows = checker._checker_expected_disk_rows()
    monkeypatch.setattr(subject, "_truth_definitions", lambda: ())
    monkeypatch.setattr(subject, "_independent_expected", lambda *_: ("passed", "", "drift"))
    assert checker._checker_truth_definitions() == before_definitions
    assert checker._checker_expected_disk_rows() == before_rows


def test_checker_independent_ast_protection_rejects_interface_reference() -> None:
    checker._check_checker_independent_ast()
    source = CHECKER_PATH.read_text()
    source = source.replace(
        'def _checker_bool(value: bool) -> str:\n    return "true" if value else "false"',
        'def _checker_bool(value: bool) -> str:\n    leaked = interface.SCALAR_REASONS\n    return "true" if value else "false"',
        1,
    )
    with pytest.raises(AssertionError, match="checker-independent"):
        checker._assert_checker_independent_ast(ast.parse(source))


def test_production_ordered_predecessor_comparison_rejects_reorder_and_substitution() -> None:
    predecessor = [dict(row) for row in _committed_predecessor_truth_rows()]
    reordered = list(predecessor)
    reordered[0], reordered[1] = reordered[1], reordered[0]
    with pytest.raises(ValueError, match="ordered predecessor truth mismatch"):
        subject._truth_rows(reordered)
    substituted = [dict(row) for row in predecessor]
    substituted[3]["scalar_input_kind"] = substituted[4]["scalar_input_kind"]
    substituted[3]["scalar_input_display"] = substituted[4]["scalar_input_display"]
    with pytest.raises(ValueError, match="ordered predecessor truth mismatch"):
        subject._truth_rows(substituted)


def test_checker_rejects_premature_admit007_unified_coverage_removal() -> None:
    snapshot = subject.build_frozen_source_snapshot()
    predecessor = tuple(
        dict(row) for row in subject._validate_predecessors(snapshot)["issue_rows"]
    )
    observed = [dict(row) for row in predecessor]
    coverage = next(
        row for row in observed
        if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    )
    coverage["affected_rules"] = "|".join(f"ADMIT_{index:03d}" for index in range(8, 16))
    coverage["integration_transition"] = "admit_007_removed_too_early"
    with pytest.raises(AssertionError, match="issue inventory not preserved"):
        checker._verify_issue_inventory_preservation(observed, predecessor)


def test_corrected_issue_bytes_exactly_equal_committed_predecessor_inventory() -> None:
    snapshot = subject.build_frozen_source_snapshot()
    predecessor = subject._validate_predecessors(snapshot)["issue_rows"]
    state = subject.build_interface_state(snapshot)
    expected_bytes = subject._record(snapshot, subject.PREDECESSOR_ISSUE_PATH).content_bytes
    observed_bytes = subject._csv_bytes(subject.ISSUE_COLUMNS, state["issue_rows"])
    assert observed_bytes == expected_bytes
    assert hashlib.sha256(observed_bytes).hexdigest() == "e63c1b83fe245031ecdefa6b3387086b2aba8d72ef50189be17b9874e8f18196"
    assert state["issue_rows"] == [dict(row) for row in predecessor]


def _validate_output_tree(root: Path, expected: dict[str, bytes]) -> None:
    assert root.is_dir() and not root.is_symlink()
    entries = tuple(root.iterdir())
    assert {entry.name for entry in entries} == set(subject.OUTPUT_FILES)
    assert all(entry.is_file() and not entry.is_symlink() for entry in entries)
    for name, payload in expected.items():
        assert (root / name).read_bytes() == payload
    manifest = json.loads((root / subject.MANIFEST_FILENAME).read_text())
    assert manifest["output_files"] == list(subject.OUTPUT_FILES)
    assert manifest["output_file_count"] == 6
    assert manifest["readiness"] == subject.READINESS
    assert manifest["all_checks_passed"] is True
    assert subject.MANIFEST_FILENAME not in manifest["output_sha256"]
    for name in subject.CSV_OUTPUTS:
        assert manifest["output_sha256"][name] == hashlib.sha256((root / name).read_bytes()).hexdigest()


def test_deterministic_double_materialization_and_exact_output_set(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    result = subject.run_covapie_bulk_download_admission_admit_007_rule_logic_interface_v1(root)
    expected, _ = subject._payloads(result["state"])
    first = {name: (root / name).read_bytes() for name in subject.OUTPUT_FILES}
    subject.run_covapie_bulk_download_admission_admit_007_rule_logic_interface_v1(root)
    second = {name: (root / name).read_bytes() for name in subject.OUTPUT_FILES}
    assert first == second == expected
    _validate_output_tree(root, expected)


@pytest.mark.parametrize("mutation", ("missing", "extra", "symlink", "tamper", "overclaim", "truth_rehash"))
def test_output_validation_fails_closed_on_mutation(tmp_path: Path, mutation: str) -> None:
    root = tmp_path / "outputs"
    result = subject.run_covapie_bulk_download_admission_admit_007_rule_logic_interface_v1(root)
    expected, _ = subject._payloads(result["state"])
    if mutation == "missing":
        (root / subject.CONTRACT_FILENAME).unlink()
    elif mutation == "extra":
        (root / "extra.txt").write_text("extra")
    elif mutation == "symlink":
        target = tmp_path / "outside"
        target.write_text("outside")
        (root / subject.CONTRACT_FILENAME).unlink()
        (root / subject.CONTRACT_FILENAME).symlink_to(target)
    elif mutation == "tamper":
        (root / subject.TRUTH_FILENAME).write_bytes(b"tampered\n")
    elif mutation == "overclaim":
        path = root / subject.MANIFEST_FILENAME
        manifest = json.loads(path.read_text())
        manifest["readiness"]["ready_for_training"] = True
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    else:
        path = root / subject.TRUTH_FILENAME
        rows = list(csv.DictReader(io.StringIO(path.read_text(), newline="")))
        rows[0]["observed_outcome"] = "blocked"
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=subject.TRUTH_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        path.write_text(stream.getvalue())
        manifest_path = root / subject.MANIFEST_FILENAME
        manifest = json.loads(manifest_path.read_text())
        manifest["output_sha256"][subject.TRUTH_FILENAME] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises((AssertionError, OSError, ValueError, json.JSONDecodeError)):
        _validate_output_tree(root, expected)


def test_materializer_rejects_unsafe_existing_output_entries(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.write_text("unchanged")
    (root / subject.CONTRACT_FILENAME).symlink_to(outside)
    with pytest.raises(ValueError):
        subject.run_covapie_bulk_download_admission_admit_007_rule_logic_interface_v1(root)
    assert outside.read_text() == "unchanged"


def test_manifest_readiness_is_exact_and_fail_closed() -> None:
    assert subject.READINESS == {
        "admit_007_standalone_evaluator_implemented": True,
        "admit_007_formal_result_contract_frozen": True,
        "admit_007_scalar_semantics_implemented": True,
        "admit_007_context_semantics_implemented": True,
        "admit_007_reason_outcome_contract_implemented": True,
        "admit_007_independent_semantic_oracle_attested": True,
        "admit_007_synthetic_truth_matrix_passed": True,
        "ready_for_admit_007_unified_adapter_contract_design": True,
        "feature_semantics_audit_required_before_training": True,
        "evaluator_call_graph_pure_in_memory": True,
        "admit_007_unified_adapter_contract_frozen": False,
        "admit_007_unified_adapter_implemented": False,
        "admit_007_registered_in_engine": False,
        "current_exact6_runtime_modified": False,
        "admit_008_standalone_evaluator_implemented": False,
        "admit_008_to_015_registered_in_engine": False,
        "all_15_rules_covered": False,
        "evaluate_all_rules_implemented": False,
        "combined_candidate_verdict_contract_frozen": False,
        "combined_candidate_verdict_implemented": False,
        "cross_rule_precedence_frozen": False,
        "real_provider_enum_mapping_validated": False,
        "real_candidate_evaluation": False,
        "exact11_real_rows_evaluated": False,
        "ready_for_bulk_download_now": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
    }


def test_production_import_is_silent_and_has_no_materialization_side_effect(tmp_path: Path) -> None:
    command = [sys.executable, "-c", "import covalent_ext.covapie_bulk_download_admission_admit_007_rule_logic_interface"]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(subject.REPO_ROOT / "src")
    completed = subprocess.run(command, cwd=tmp_path, env=environment, capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == ""
    assert tuple(tmp_path.iterdir()) == ()
