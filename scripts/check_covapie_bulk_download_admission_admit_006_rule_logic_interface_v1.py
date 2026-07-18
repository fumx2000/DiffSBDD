#!/usr/bin/env python3
"""Fail-closed checker for the ADMIT_006 standalone evaluator interface v1."""

from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import inspect
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import FrozenInstanceError, dataclass, fields, replace
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_006_rule_logic_interface as interface,
)


EXPECTED_OUTPUT_SHA256 = {
    interface.CONTRACT_FILENAME: "b19c251567e2d1b56d425e6dbcdca1a77c7238c026b7786b00ade429682ab792",
    interface.TRUTH_FILENAME: "793d754f81a54bb785e74665893651e02c5bb12d01d877d43ff3007cc2fc8b02",
    interface.SOURCE_AUDIT_FILENAME: "8e84fc0c9d1aa65518560def20fcff3be27396d2fe82a197f855046ec576f0d1",
    interface.SAFETY_FILENAME: "07bc81df2603f01926239edda811447c56abce98193c2505d21e557770bb7cc0",
    interface.ISSUE_FILENAME: "d3333fd74af79b065eb136d830e730c3a636e0d632bcb735b3e841a29d548c79",
    interface.MANIFEST_FILENAME: "921356eaa15f40fed925d11d73a6fbb868b4c881828c358fb35fde168b8c33f8",
}

CHECKER_ENUM_MEMBERS = (
    "explicit_structure_bond_record",
    "explicit_curated_covalent_annotation",
    "distance_only_inference",
)
CHECKER_ALLOWED_CONTEXT = (
    "explicit_structure_bond_record",
    "explicit_curated_covalent_annotation",
)
CHECKER_SCALAR_SYNTAX = r"[a-z][a-z0-9_]{0,63}"
CHECKER_SCALAR_REASONS = (
    "COVALENT_EVENT_EVIDENCE_SOURCE_TYPE_INVALID",
    "COVALENT_EVENT_EVIDENCE_SOURCE_EMPTY",
    "COVALENT_EVENT_EVIDENCE_SOURCE_NON_ASCII",
    "COVALENT_EVENT_EVIDENCE_SOURCE_SYNTAX_INVALID",
    "COVALENT_EVENT_EVIDENCE_SOURCE_UNKNOWN",
)
CHECKER_CONTEXT_REASONS = (
    "ALLOWED_COVALENT_EVIDENCE_CLASSES_TYPE_INVALID",
    "ALLOWED_COVALENT_EVIDENCE_CLASSES_CONTENT_INVALID",
)
CHECKER_BLOCKED_REASON = "COVALENT_EVENT_EVIDENCE_NOT_EXPLICIT"
CHECKER_CANDIDATE_FIELDS = ("covalent_event_evidence_source",)
CHECKER_CONTEXT_ITEMS = ("allowed_covalent_evidence_classes",)
CHECKER_RESULT_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_covalent_event_evidence_source",
    "validated_candidate_fields",
    "consumed_candidate_fields",
    "consumed_context_items",
    "evaluator_io_used",
)
CHECKER_TRUTH_COLUMNS = (
    "case_id", "case_group", "scalar_input_kind", "scalar_input_display",
    "context_input_kind", "context_input_display", "expected_outcome", "expected_reason",
    "observed_outcome", "observed_reason", "expected_canonical_evidence_source",
    "observed_canonical_evidence_source", "expected_validated_candidate_fields",
    "observed_validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "case_passed",
)
CHECKER_GROUP_COUNTS = {
    "canonical": 3,
    "scalar_type": 6,
    "empty_syntax": 11,
    "unknown": 5,
    "context": 12,
}


@dataclass(frozen=True)
class CheckerExpectedResult:
    admission_rule_id: str
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    canonical_covalent_event_evidence_source: str
    validated_candidate_fields: tuple[tuple[str, str], ...]
    consumed_candidate_fields: tuple[str, ...]
    consumed_context_items: tuple[str, ...]
    evaluator_io_used: bool


class _StringSubclass(str):
    """Checker-owned exact-str-subclass negative."""


def _assert(condition: bool, message: str) -> None:
    if condition is not True:
        raise AssertionError(message)


def _result_tuple(result: interface.Admit006EvaluationResult) -> tuple[Any, ...]:
    return tuple(getattr(result, field.name) for field in fields(result))


def _checker_bool(value: bool) -> str:
    return "true" if value else "false"


def _checker_scalar_state(scalar: object) -> tuple[str, str, str]:
    if type(scalar) is not str:
        return "invalid", "", CHECKER_SCALAR_REASONS[0]
    elif len(scalar) == 0:
        return "invalid", "", CHECKER_SCALAR_REASONS[1]
    elif not all(ord(character) < 128 for character in scalar):
        return "invalid", "", CHECKER_SCALAR_REASONS[2]
    elif re.fullmatch(CHECKER_SCALAR_SYNTAX, scalar, flags=re.ASCII) is None:
        return "invalid", "", CHECKER_SCALAR_REASONS[3]
    elif scalar not in CHECKER_ENUM_MEMBERS:
        return "unknown", "", CHECKER_SCALAR_REASONS[4]
    return "canonical", scalar, ""


def _checker_context_state(context: object) -> tuple[bool, str]:
    if type(context) is not tuple:
        return False, CHECKER_CONTEXT_REASONS[0]
    if (
        len(context) != 2
        or type(context[0]) is not str
        or type(context[1]) is not str
        or context != CHECKER_ALLOWED_CONTEXT
    ):
        return False, CHECKER_CONTEXT_REASONS[1]
    return True, ""


def _checker_oracle(scalar: object, context: object) -> CheckerExpectedResult:
    scalar_classification, canonical, scalar_reason = _checker_scalar_state(scalar)
    context_valid, context_reason = _checker_context_state(context)
    if scalar_classification != "canonical":
        outcome, reason = "invalid", scalar_reason
    elif not context_valid:
        outcome, reason = "invalid", context_reason
    elif canonical == "distance_only_inference":
        outcome, reason = "blocked", CHECKER_BLOCKED_REASON
    else:
        outcome, reason = "passed", ""
    validated = () if canonical == "" else ((CHECKER_CANDIDATE_FIELDS[0], canonical),)
    return CheckerExpectedResult(
        "ADMIT_006", outcome, outcome == "passed", outcome != "passed", reason,
        canonical, validated, CHECKER_CANDIDATE_FIELDS, CHECKER_CONTEXT_ITEMS, False,
    )


def _checker_display(value: object) -> str:
    if type(value) is str:
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, _StringSubclass):
        return f"str_subclass:{json.dumps(str(value))}"
    if type(value) in (tuple, list):
        return f"{type(value).__name__}:{json.dumps(list(value), ensure_ascii=True)}"
    if type(value) in (set, frozenset):
        return f"{type(value).__name__}:{json.dumps(sorted(value), ensure_ascii=True)}"
    if type(value) is dict:
        return f"dict:{json.dumps(value, ensure_ascii=True, sort_keys=True)}"
    return f"{type(value).__name__}:{repr(value)}"


def _checker_predecessor_display(value: object) -> str:
    if type(value) is str:
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, _StringSubclass):
        return f"str_subclass:{json.dumps(str(value))}"
    return f"{type(value).__name__}:{repr(value)}"


def _checker_truth_definitions() -> tuple[tuple[str, str, object, str, object], ...]:
    exact = CHECKER_ALLOWED_CONTEXT
    scalar_cases: tuple[tuple[str, str, object], ...] = (
        ("canonical_structure_bond", "canonical", CHECKER_ENUM_MEMBERS[0]),
        ("canonical_curated_annotation", "canonical", CHECKER_ENUM_MEMBERS[1]),
        ("canonical_distance_only", "canonical", CHECKER_ENUM_MEMBERS[2]),
        ("type_none", "scalar_type", None), ("type_int", "scalar_type", 7),
        ("type_bool", "scalar_type", True),
        ("type_str_subclass", "scalar_type", _StringSubclass(CHECKER_ENUM_MEMBERS[0])),
        ("type_list", "scalar_type", [CHECKER_ENUM_MEMBERS[0]]),
        ("type_mapping", "scalar_type", {"value": CHECKER_ENUM_MEMBERS[0]}),
        ("empty", "empty_syntax", ""), ("whitespace_only", "empty_syntax", " "),
        ("leading_whitespace", "empty_syntax", " explicit_structure_bond_record"),
        ("trailing_whitespace", "empty_syntax", "explicit_structure_bond_record "),
        ("uppercase", "empty_syntax", "Explicit_structure_bond_record"),
        ("hyphen", "empty_syntax", "explicit-structure-bond-record"),
        ("dot", "empty_syntax", "explicit.structure"),
        ("slash", "empty_syntax", "explicit/structure"),
        ("non_ascii", "empty_syntax", "explicit_évidence"),
        ("over_length", "empty_syntax", "a" * 65),
        ("leading_digit", "empty_syntax", "1explicit"),
        ("unknown_valid", "unknown", "unregistered_value"),
        ("unknown_explicit_looking", "unknown", "explicit_database_bond"),
        ("unknown_manual_review", "unknown", "manual_review"),
        ("unknown_other", "unknown", "other"),
        ("unknown_unknown", "unknown", "unknown"),
    )
    context_cases: tuple[tuple[str, object], ...] = (
        ("context_exact_tuple", exact), ("context_none", None),
        ("context_list", list(exact)), ("context_set", set(exact)),
        ("context_frozenset", frozenset(exact)),
        ("context_wrong_order", tuple(reversed(exact))),
        ("context_missing_member", exact[:1]),
        ("context_duplicate", (exact[0], exact[0])),
        ("context_distance_only", (*exact, CHECKER_ENUM_MEMBERS[2])),
        ("context_unknown", (*exact, "unknown")),
        ("context_str_subclass", (_StringSubclass(exact[0]), exact[1])),
        ("context_extra_member", (*exact, "explicit_database_bond")),
    )
    definitions = [
        (case_id, group, scalar, "exact_tuple", exact)
        for case_id, group, scalar in scalar_cases
    ]
    definitions.extend(
        (case_id, "context", CHECKER_ENUM_MEMBERS[0], case_id.removeprefix("context_"), context)
        for case_id, context in context_cases
    )
    return tuple(definitions)


def _checker_expected_disk_rows() -> tuple[dict[str, str], ...]:
    rows = []
    for index, (name, group, scalar, context_kind, context) in enumerate(
        _checker_truth_definitions(), 1
    ):
        result = _checker_oracle(scalar, context)
        validated_json = json.dumps(result.validated_candidate_fields, separators=(",", ":"))
        rows.append({
            "case_id": f"CASE_{index:03d}_{name}",
            "case_group": group,
            "scalar_input_kind": type(scalar).__name__,
            "scalar_input_display": _checker_display(scalar),
            "context_input_kind": context_kind,
            "context_input_display": _checker_display(context),
            "expected_outcome": result.outcome,
            "expected_reason": result.reason,
            "observed_outcome": result.outcome,
            "observed_reason": result.reason,
            "expected_canonical_evidence_source": result.canonical_covalent_event_evidence_source,
            "observed_canonical_evidence_source": result.canonical_covalent_event_evidence_source,
            "expected_validated_candidate_fields": validated_json,
            "observed_validated_candidate_fields": validated_json,
            "consumed_candidate_fields": "|".join(result.consumed_candidate_fields),
            "consumed_context_items": "|".join(result.consumed_context_items),
            "evaluator_io_used": _checker_bool(result.evaluator_io_used),
            "case_passed": "true",
        })
    return tuple(rows)


def _checker_expected_predecessor_rows() -> tuple[dict[str, str], ...]:
    rows = []
    for index, (name, group, scalar, context_kind, context) in enumerate(
        _checker_truth_definitions(), 1
    ):
        scalar_classification, canonical, scalar_reason = _checker_scalar_state(scalar)
        context_valid, context_reason = _checker_context_state(context)
        result = _checker_oracle(scalar, context)
        rows.append({
            "case_id": f"CASE_{index:03d}_{name}",
            "case_group": group,
            "scalar_input_kind": type(scalar).__name__,
            "scalar_input_display": _checker_predecessor_display(scalar),
            "context_input_kind": context_kind,
            "expected_scalar_classification": scalar_classification,
            "expected_canonical_value": canonical,
            "expected_scalar_reason": scalar_reason,
            "expected_context_valid": _checker_bool(context_valid),
            "expected_context_reason": context_reason,
            "expected_admit_006_outcome": result.outcome,
            "expected_admit_006_reason": result.reason,
            "normative_not_observed": "true",
            "case_passed": "true",
        })
    return tuple(rows)


def _result_values(
    outcome: str, reason: str, canonical: str,
    validated: tuple[tuple[str, str], ...] | None = None,
) -> dict[str, Any]:
    expected = () if canonical == "" else ((interface.CANDIDATE_FIELDS[0], canonical),)
    return {
        "admission_rule_id": "ADMIT_006",
        "outcome": outcome,
        "passed": outcome == "passed",
        "blocks_candidate": outcome != "passed",
        "reason": reason,
        "canonical_covalent_event_evidence_source": canonical,
        "validated_candidate_fields": expected if validated is None else validated,
        "consumed_candidate_fields": interface.CANDIDATE_FIELDS,
        "consumed_context_items": interface.CONTEXT_ITEMS,
        "evaluator_io_used": False,
    }


def _check_public_contract() -> int:
    signature = inspect.signature(interface.evaluate_admit_006)
    parameters = tuple(signature.parameters.values())
    _assert(
        tuple(parameter.name for parameter in parameters)
        == ("covalent_event_evidence_source", "allowed_covalent_evidence_classes"),
        "public parameter names",
    )
    _assert(all(parameter.default is inspect.Parameter.empty for parameter in parameters), "defaults forbidden")
    _assert(
        all(parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD for parameter in parameters),
        "parameter kinds",
    )
    _assert(tuple(field.name for field in fields(interface.Admit006EvaluationResult)) == CHECKER_RESULT_FIELDS, "Exact10 result fields")
    _assert(interface.OUTCOME_VOCABULARY == ("passed", "blocked", "invalid"), "outcome vocabulary")
    _assert(interface.CANONICAL_ENUM_MEMBERS == CHECKER_ENUM_MEMBERS, "Exact3 enum")
    _assert(interface.ALLOWED_COVALENT_EVIDENCE_CLASSES == CHECKER_ALLOWED_CONTEXT, "Exact2 context")
    _assert(interface.SCALAR_REASONS == CHECKER_SCALAR_REASONS, "scalar reasons")
    _assert(interface.CONTEXT_REASONS == CHECKER_CONTEXT_REASONS, "context reasons")
    _assert(interface.BLOCKED_REASON == CHECKER_BLOCKED_REASON, "blocked reason")
    _assert(interface.CANDIDATE_FIELDS == CHECKER_CANDIDATE_FIELDS, "candidate fields")
    _assert(interface.CONTEXT_ITEMS == CHECKER_CONTEXT_ITEMS, "context items")
    _assert(interface.TRUTH_COLUMNS == CHECKER_TRUTH_COLUMNS, "Exact18 truth columns")

    result = interface.evaluate_admit_006(
        interface.CANONICAL_ENUM_MEMBERS[0], interface.ALLOWED_COVALENT_EVIDENCE_CLASSES
    )
    try:
        result.reason = "changed"  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("result dataclass is mutable")

    conflicts = (
        _result_values("passed", "", "distance_only_inference"),
        _result_values("blocked", interface.BLOCKED_REASON, "explicit_structure_bond_record"),
        _result_values("invalid", interface.SCALAR_REASONS[0], "explicit_structure_bond_record"),
        _result_values("invalid", interface.CONTEXT_REASONS[0], ""),
        _result_values("invalid", interface.CONTEXT_REASONS[1], "explicit_structure_bond_record", ()),
        _result_values("invalid", interface.SCALAR_REASONS[4], "", (("covalent_event_evidence_source", "unknown"),)),
        _result_values("invalid", "", ""),
        _result_values("blocked", "", "distance_only_inference"),
    )
    for values in conflicts:
        try:
            interface.Admit006EvaluationResult(**values)
        except (TypeError, ValueError):
            continue
        raise AssertionError("semantic result conflict accepted")
    return len(conflicts)


def _check_exact37_semantics() -> None:
    definitions = _checker_truth_definitions()
    _assert(len(definitions) == 37, "Exact37 definition count")
    counts = {group: sum(case[1] == group for case in definitions) for group in (
        "canonical", "scalar_type", "empty_syntax", "unknown", "context"
    )}
    _assert(counts == CHECKER_GROUP_COUNTS, "Exact37 groups")
    for _, _, scalar, _, context in definitions:
        before = (repr(scalar), repr(context))
        first = interface.evaluate_admit_006(scalar, context)
        second = interface.evaluate_admit_006(scalar, context)
        _assert(first == second, "evaluator not deterministic")
        _assert((repr(scalar), repr(context)) == before, "input mutation")
        expected = _checker_oracle(scalar, context)
        expected_tuple = tuple(getattr(expected, name) for name in CHECKER_RESULT_FIELDS)
        _assert(_result_tuple(first) == expected_tuple, "independent oracle mismatch")
    precedence = interface.evaluate_admit_006("UNKNOWN", None)
    _assert(precedence.reason == CHECKER_SCALAR_REASONS[3], "scalar/context precedence")
    distance = interface.evaluate_admit_006("distance_only_inference", CHECKER_ALLOWED_CONTEXT)
    _assert(distance.outcome == "blocked" and distance.reason == CHECKER_BLOCKED_REASON, "distance-only classification")
    for explicit in CHECKER_ALLOWED_CONTEXT:
        observed = interface.evaluate_admit_006(explicit, CHECKER_ALLOWED_CONTEXT)
        _assert(observed.outcome == "passed" and observed.reason == "", "explicit classification")


def _verify_exact37_views(
    predecessor_rows: tuple[dict[str, str], ...],
    disk_rows: tuple[dict[str, str], ...],
) -> None:
    definitions = _checker_truth_definitions()
    expected_predecessor = _checker_expected_predecessor_rows()
    expected_disk = _checker_expected_disk_rows()
    _assert(len(definitions) == len(expected_predecessor) == len(expected_disk) == 37, "independent Exact37 shape")
    _assert(len(predecessor_rows) == 37, "committed predecessor Exact37 shape")
    _assert(len(disk_rows) == 37, "materialized disk Exact37 shape")
    for index, (definition, expected_result_row, expected_prior, prior, disk) in enumerate(
        zip(definitions, expected_disk, expected_predecessor, predecessor_rows, disk_rows, strict=True), 1
    ):
        _assert(
            all(prior.get(key) == value for key, value in expected_prior.items()),
            f"committed predecessor mismatch at row {index}",
        )
        _assert(tuple(disk) == CHECKER_TRUTH_COLUMNS, f"disk truth columns at row {index}")
        _assert(disk == expected_result_row, f"materialized disk mismatch at row {index}")
        _, _, scalar, _, context = definition
        observed = interface.evaluate_admit_006(scalar, context)
        expected = _checker_oracle(scalar, context)
        _assert(
            _result_tuple(observed)
            == tuple(getattr(expected, name) for name in CHECKER_RESULT_FIELDS),
            f"production evaluator mismatch at row {index}",
        )


def _verify_issue_inventory_preservation(
    observed_rows: list[dict[str, str]],
    predecessor_rows: tuple[dict[str, str], ...],
) -> None:
    _assert(len(observed_rows) == len(predecessor_rows) == 11, "Exact11 issue shape")
    _assert(observed_rows == [dict(row) for row in predecessor_rows], "issue inventory not preserved")
    coverage = [
        row for row in observed_rows
        if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    ]
    _assert(len(coverage) == 1, "unified coverage issue identity")
    _assert(coverage[0]["status"] == "open", "unified coverage issue status")
    _assert(coverage[0]["blocking_scope"] == "unified_admission_engine", "unified coverage issue scope")
    _assert(
        coverage[0]["affected_rules"]
        == "ADMIT_006|ADMIT_007|ADMIT_008|ADMIT_009|ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        "unified coverage issue rules",
    )
    _assert(
        coverage[0]["integration_transition"]
        == "admit_005_implemented_and_removed_from_open_coverage_scope",
        "unified coverage predecessor transition",
    )


def _called_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                names.add(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                names.add(child.func.attr)
    return names


def _pure_closure(tree: ast.Module, root: str) -> set[str]:
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    banned = {
        "classify_admit_006_admit_007_evidence_design", "build_interface_state",
        "run_covapie_bulk_download_admission_admit_006_rule_logic_interface_v1",
        "build_frozen_source_snapshot", "_git", "open", "read", "read_bytes", "read_text",
        "write", "write_bytes", "write_text", "run", "Popen", "system", "urlopen", "request",
        "evaluate_rule", "register", "provider",
    }
    pending = [root]
    closure: set[str] = set()
    while pending:
        name = pending.pop()
        if name in closure:
            continue
        _assert(name in functions, f"missing call-graph node: {name}")
        closure.add(name)
        calls = _called_names(functions[name])
        _assert(not calls.intersection(banned), f"banned evaluator call: {calls.intersection(banned)}")
        pending.extend(call for call in calls if call in functions)
    return closure


CHECKER_INDEPENDENT_FUNCTIONS = (
    "_checker_bool",
    "_checker_scalar_state",
    "_checker_context_state",
    "_checker_oracle",
    "_checker_display",
    "_checker_predecessor_display",
    "_checker_truth_definitions",
    "_checker_expected_disk_rows",
    "_checker_expected_predecessor_rows",
)


def _assert_checker_independent_ast(tree: ast.Module) -> None:
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    banned_names = {
        "interface",
        "_truth_definitions",
        "_independent_expected",
        "_truth_rows",
        "classify_admit_006_admit_007_evidence_design",
    }
    for name in CHECKER_INDEPENDENT_FUNCTIONS:
        _assert(name in functions, f"missing checker-independent function: {name}")
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Name):
                _assert(node.id not in banned_names, f"checker-independent name leak in {name}: {node.id}")
            if isinstance(node, ast.Attribute):
                _assert(node.attr not in banned_names, f"checker-independent attribute leak in {name}: {node.attr}")
                root = node.value
                while isinstance(root, ast.Attribute):
                    root = root.value
                _assert(
                    not isinstance(root, ast.Name) or root.id != "interface",
                    f"checker-independent interface reference in {name}",
                )


def _check_checker_independent_ast() -> None:
    checker_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    _assert_checker_independent_ast(checker_tree)


def _check_evaluator_call_graph() -> None:
    production_path = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_006_rule_logic_interface.py"
    tree = ast.parse(production_path.read_text(encoding="utf-8"))
    closure = _pure_closure(tree, "evaluate_admit_006")
    _assert(closure == {"evaluate_admit_006", "_validate_scalar", "_validate_context", "_result"}, "unexpected evaluator closure")
    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.split(".")[0])
    standard = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}
    _assert(all(name in standard for name in imports), "non-stdlib production import")
    for bad in (
        "classify_admit_006_admit_007_evidence_design(x)", "read_bytes(x)", "build_interface_state()"
    ):
        synthetic = ast.parse(f"def evaluate_admit_006(x):\n    return helper(x)\ndef helper(x):\n    return {bad}\n")
        try:
            _pure_closure(synthetic, "evaluate_admit_006")
        except AssertionError:
            continue
        raise AssertionError("call-graph negative accepted")


def _check_snapshot_and_state() -> dict[str, Any]:
    original_git = interface._git
    structural_count = 0
    first_content_read_after = -1

    def observed_git(arguments: Any, repo_root: Path, *, text: bool = True) -> Any:
        nonlocal structural_count, first_content_read_after
        if tuple(arguments[:2]) == ("ls-files", "--error-unmatch"):
            structural_count += 1
        if arguments[0] == "show" and len(arguments) == 2 and ":" in arguments[1] and first_content_read_after == -1:
            first_content_read_after = structural_count
        return original_git(arguments, repo_root, text=text)

    interface._git = observed_git
    try:
        snapshot = interface.build_frozen_source_snapshot()
    finally:
        interface._git = original_git
    _assert(structural_count == first_content_read_after == len(interface.SOURCE_PATHS), "structural checks did not precede bytes")
    _assert(interface.validate_frozen_source_snapshot(snapshot), "source snapshot invalid")

    first = snapshot.records[0]
    bad_record = replace(first, content_bytes=first.content_bytes + b"tamper")
    bad_snapshot = interface.FrozenSourceSnapshot((bad_record, *snapshot.records[1:]))
    _assert(not interface.validate_frozen_source_snapshot(bad_snapshot), "source SHA mismatch accepted")

    def non_descendant(arguments: Any, repo_root: Path, *, text: bool = True) -> Any:
        if tuple(arguments[:2]) == ("merge-base", "--is-ancestor"):
            empty = "" if text else b""
            return subprocess.CompletedProcess(arguments, 1, empty, empty)
        return original_git(arguments, repo_root, text=text)

    interface._git = non_descendant
    try:
        try:
            interface.build_frozen_source_snapshot()
        except ValueError as error:
            _assert("not an ancestor" in str(error), "wrong non-descendant failure")
        else:
            raise AssertionError("non-descendant base accepted")
    finally:
        interface._git = original_git

    state = interface.build_interface_state(snapshot)
    predecessor_record = next(
        record for record in snapshot.records
        if record.relative_path == interface.PREDECESSOR_TRUTH_PATH
    )
    predecessor_reader = csv.DictReader(
        io.StringIO(predecessor_record.content_bytes.decode("utf-8"), newline="")
    )
    predecessor_rows = tuple(dict(row) for row in predecessor_reader)
    disk_reader = csv.DictReader(
        io.StringIO(
            (REPO_ROOT / interface.DEFAULT_OUTPUT_ROOT / interface.TRUTH_FILENAME).read_text(),
            newline="",
        )
    )
    disk_rows = tuple(dict(row) for row in disk_reader)
    _verify_exact37_views(predecessor_rows, disk_rows)
    _assert(tuple(state["truth_rows"]) == _checker_expected_disk_rows(), "production materialized truth drift")
    _assert(len(state["contract_rows"]) == 28, "contract count")
    _assert(len(state["truth_rows"]) == 37 and all(row["case_passed"] == "true" for row in state["truth_rows"]), "truth rows")
    _assert(len(state["source_audit_rows"]) == len(interface.SOURCE_PATHS), "source audit count")
    _assert(
        state["source_audit_rows"][4]["boundary_necessity"]
        == "ordered Exact11 issue inventory preservation baseline",
        "source boundary row 5 preservation wording",
    )
    _assert(len(state["issue_rows"]) == 11, "Exact11 issue count")
    coverage = [row for row in state["issue_rows"] if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    enum_issue = [row for row in state["issue_rows"] if row["issue_id"] == "COVALENT_EVIDENCE_ENUM_UNRESOLVED"]
    predecessor_issues = interface._validate_predecessors(snapshot)["issue_rows"]
    _verify_issue_inventory_preservation(state["issue_rows"], predecessor_issues)
    _assert(len(coverage) == 1, "coverage issue identity")
    _assert(len(enum_issue) == 1 and enum_issue[0]["status"] == "resolved", "enum issue changed")
    _assert(state["readiness"] == interface.READINESS, "readiness mismatch")
    _assert(state["readiness"]["ready_for_training"] is False, "training overclaim")
    return state


def _validate_output_tree(root: Path, expected: dict[str, bytes]) -> None:
    _assert(root.exists() and root.is_dir() and not root.is_symlink(), "unsafe output root")
    entries = tuple(root.iterdir())
    _assert({entry.name for entry in entries} == set(interface.OUTPUT_FILES), "output set mismatch")
    _assert(all(entry.is_file() and not entry.is_symlink() for entry in entries), "unsafe output entry")
    for name, payload in expected.items():
        _assert((root / name).read_bytes() == payload, f"output mismatch: {name}")
    manifest = json.loads((root / interface.MANIFEST_FILENAME).read_text())
    _assert(manifest["output_files"] == list(interface.OUTPUT_FILES), "manifest output set")
    _assert(manifest["output_file_count"] == 6, "manifest output count")
    _assert(manifest["readiness"] == interface.READINESS, "manifest readiness")
    _assert(manifest["all_checks_passed"] is True, "manifest overclaim")
    _assert(interface.MANIFEST_FILENAME not in manifest["output_sha256"], "manifest self hash")
    for name in interface.CSV_OUTPUTS:
        digest = hashlib.sha256((root / name).read_bytes()).hexdigest()
        _assert(manifest["output_sha256"].get(name) == digest, f"manifest hash: {name}")


def _expect_invalid_output(root: Path, expected: dict[str, bytes]) -> None:
    try:
        _validate_output_tree(root, expected)
    except (AssertionError, OSError, ValueError, json.JSONDecodeError):
        return
    raise AssertionError("mutated output accepted")


def _check_materialization(state: dict[str, Any]) -> dict[str, str]:
    expected, _ = interface._payloads(state)
    output_root = REPO_ROOT / interface.DEFAULT_OUTPUT_ROOT
    _validate_output_tree(output_root, expected)
    with tempfile.TemporaryDirectory(prefix="covapie-admit006-check-") as temporary:
        temporary_root = Path(temporary)
        root = temporary_root / "outputs"
        interface.run_covapie_bulk_download_admission_admit_006_rule_logic_interface_v1(root)
        first = {name: (root / name).read_bytes() for name in interface.OUTPUT_FILES}
        interface.run_covapie_bulk_download_admission_admit_006_rule_logic_interface_v1(root)
        second = {name: (root / name).read_bytes() for name in interface.OUTPUT_FILES}
        _assert(first == second == expected, "double materialization differs")
        for mutation in ("missing", "extra", "tamper", "overclaim", "truth_rehash"):
            victim = temporary_root / mutation
            shutil.copytree(root, victim)
            if mutation == "missing":
                (victim / interface.CONTRACT_FILENAME).unlink()
            elif mutation == "extra":
                (victim / "extra.txt").write_text("extra")
            elif mutation == "tamper":
                (victim / interface.TRUTH_FILENAME).write_bytes(b"tampered\n")
            elif mutation == "overclaim":
                path = victim / interface.MANIFEST_FILENAME
                manifest = json.loads(path.read_text())
                manifest["readiness"]["ready_for_training"] = True
                path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            else:
                truth_path = victim / interface.TRUTH_FILENAME
                rows = list(csv.DictReader(io.StringIO(truth_path.read_text(), newline="")))
                rows[0]["observed_outcome"] = "blocked"
                stream = io.StringIO(newline="")
                writer = csv.DictWriter(stream, fieldnames=interface.TRUTH_COLUMNS, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
                truth_path.write_text(stream.getvalue())
                manifest_path = victim / interface.MANIFEST_FILENAME
                manifest = json.loads(manifest_path.read_text())
                manifest["output_sha256"][interface.TRUTH_FILENAME] = hashlib.sha256(truth_path.read_bytes()).hexdigest()
                manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            _expect_invalid_output(victim, expected)

        unsafe = temporary_root / "symlink"
        unsafe.mkdir()
        outside = temporary_root / "outside"
        outside.write_text("unchanged")
        (unsafe / interface.CONTRACT_FILENAME).symlink_to(outside)
        try:
            interface.run_covapie_bulk_download_admission_admit_006_rule_logic_interface_v1(unsafe)
        except ValueError:
            pass
        else:
            raise AssertionError("symlink output accepted")
        _assert(outside.read_text() == "unchanged", "symlink victim modified")
    _assert(not tuple(output_root.glob("*.tmp")) and not tuple(output_root.glob("*.part")), "temporary residue")
    hashes = {
        name: hashlib.sha256((output_root / name).read_bytes()).hexdigest()
        for name in interface.OUTPUT_FILES
    }
    _assert(hashes == EXPECTED_OUTPUT_SHA256, "frozen output SHA256 mismatch")
    return hashes


def _check_generated_preservation_wording(state: dict[str, Any]) -> None:
    expected = "ordered Exact11 issue inventory preservation baseline"
    stale = "one-row coverage transition"
    _assert(state["source_audit_rows"][4]["boundary_necessity"] == expected, "row 5 wording")
    output_root = REPO_ROOT / interface.DEFAULT_OUTPUT_ROOT
    paths = tuple(output_root / name for name in interface.OUTPUT_FILES) + (
        REPO_ROOT / "docs/covapie_bulk_download_admission_admit_006_rule_logic_interface_v1_summary.md",
    )
    _assert(all(stale not in path.read_text() for path in paths), "stale transition wording remains")


def _silent_import(command_text: str) -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(SRC_ROOT)
    completed = subprocess.run(
        [sys.executable, "-c", command_text], cwd=REPO_ROOT, env=environment,
        capture_output=True, text=True, check=False,
    )
    _assert(completed.returncode == 0, "import failed")
    _assert(completed.stdout == "" and completed.stderr == "", "import emitted output")


def _check_silent_imports() -> None:
    _silent_import("import covalent_ext.covapie_bulk_download_admission_admit_006_rule_logic_interface")
    checker = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_006_rule_logic_interface_v1.py"
    command = (
        "import importlib.util,sys;"
        f"s=importlib.util.spec_from_file_location('admit006_checker',{str(checker)!r});"
        "m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)"
    )
    _silent_import(command)


def main() -> int:
    invariant_count = _check_public_contract()
    _check_exact37_semantics()
    _check_checker_independent_ast()
    _check_evaluator_call_graph()
    state = _check_snapshot_and_state()
    output_hashes = _check_materialization(state)
    _check_generated_preservation_wording(state)
    _check_silent_imports()

    _assert(len(state["truth_rows"]) == 37, "stdout truth assertion")
    print("admit_006_truth_matrix=37/37")
    print("admit_006_truth_groups=canonical:3,scalar_type:6,empty_syntax:11,unknown:5,context:12")
    _assert(len(state["contract_rows"]) == 28, "stdout contract assertion")
    print("admit_006_contract=28/28")
    _assert(len(state["source_audit_rows"]) == len(interface.SOURCE_PATHS), "stdout source assertion")
    print(f"source_boundary={len(interface.SOURCE_PATHS)}/{len(interface.SOURCE_PATHS)}")
    _assert(len(state["issue_rows"]) == 11, "stdout issue assertion")
    print("exact11_issue_inventory=11/11")
    _assert(invariant_count == 8, "stdout invariant assertion")
    print("direct_result_semantic_invariants=8/8")
    _assert(state["readiness"]["ready_for_training"] is False, "stdout readiness assertion")
    print("ready_for_training=false")
    for name in interface.OUTPUT_FILES:
        _assert(output_hashes[name] == EXPECTED_OUTPUT_SHA256[name], "stdout hash assertion")
        print(f"sha256 {name} {output_hashes[name]}")
    print("ADMIT_006_STANDALONE_EVALUATOR_INTERFACE_CHECK=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
