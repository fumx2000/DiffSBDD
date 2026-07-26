"""Targeted tests for the pure CovaPIE combined aggregation runtime."""

from __future__ import annotations

import ast
import builtins
import ctypes
import dataclasses
import hashlib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1
    as production,
)
from covalent_ext import (
    covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004
    as owner,
)
from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015
    as exact15,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    ROOT
    / "scripts"
    / "check_covapie_bulk_download_admission_combined_candidate_verdict_and_"
    "cross_rule_aggregation_v1.py"
)
SPEC = importlib.util.spec_from_file_location("combined_implementation_checker", CHECKER_PATH)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)

FIELDS = production.RESULT_FIELDS
SCOPES = production.SCOPE_IDS
REQUIRED = production.REQUIRED_RULE_IDS


def git(root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, (
        arguments,
        completed.stdout,
        completed.stderr,
    )
    return completed.stdout


def git_with_input(
    root: Path,
    input_bytes: bytes,
    *arguments: str,
) -> bytes:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=root,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, (
        arguments,
        completed.stdout,
        completed.stderr,
    )
    return completed.stdout


def synthetic_other_commit(root: Path, parent: str) -> str:
    tree = git(root, "rev-parse", f"{parent}^{{tree}}").decode().strip()
    return git(
        root,
        "commit-tree",
        tree,
        "-p",
        parent,
        "-m",
        "synthetic other commit",
    ).decode().strip()


def valid_platform_capture_ref() -> str:
    return (
        f"{checker.PLATFORM_REF_NAMESPACE}/captures/1234567890123/"
        "12345678-1234-4234-8234-123456789abc/base"
    )


def write_synthetic_exact10(root: Path) -> None:
    for order, relative in enumerate(checker.EXACT10, 1):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"synthetic-exact10-{order}\n".encode())


def synthetic_base(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "CovaPIE Test")
    git(root, "config", "user.email", "covapie-test@example.invalid")
    raw = root / "data/raw"
    raw.mkdir(parents=True)
    for number in range(53):
        (raw / f"historical-{number:02d}.txt").write_bytes(b"raw\n")
    git(root, "add", "--", "data/raw")
    git(root, "commit", "-m", "synthetic base")
    return root, git(root, "rev-parse", "HEAD").decode().strip()


def synthetic_precommit(tmp_path: Path) -> tuple[Path, str]:
    root, base = synthetic_base(tmp_path)
    write_synthetic_exact10(root)
    assert set(
        checker._nul_paths(
            git(
                root,
                "ls-files",
                "--others",
                "--exclude-standard",
                "-z",
            ),
            "synthetic untracked",
        )
    ) == {path.as_posix() for path in checker.EXACT10}
    return root, base


def synthetic_formal_postcommit(
    tmp_path: Path,
) -> tuple[Path, str, str]:
    root, base = synthetic_precommit(tmp_path)
    git(root, "add", "--", *(path.as_posix() for path in checker.EXACT10))
    git(root, "commit", "-m", "synthetic Exact10 candidate")
    return root, base, git(root, "rev-parse", "HEAD").decode().strip()


def synthetic_detached_postcommit(
    tmp_path: Path,
) -> tuple[Path, Path, str, str]:
    main, base = synthetic_base(tmp_path)
    candidate = tmp_path / "candidate"
    git(main, "worktree", "add", "--detach", str(candidate), base)
    write_synthetic_exact10(candidate)
    git(
        candidate,
        "add",
        "--",
        *(path.as_posix() for path in checker.EXACT10),
    )
    git(candidate, "commit", "-m", "synthetic detached Exact10 candidate")
    head = git(candidate, "rev-parse", "HEAD").decode().strip()
    return main, candidate, base, head


def ignore_path(root: Path, relative: Path) -> None:
    exclude = root / ".git/info/exclude"
    with exclude.open("ab") as stream:
        stream.write(f"/{relative.as_posix()}\n".encode())


def synthetic_untracked(root: Path) -> set[str]:
    return set(
        checker._nul_paths(
            git(
                root,
                "ls-files",
                "--others",
                "--exclude-standard",
                "-z",
            ),
            "synthetic untracked",
        )
    )


def evaluation(
    rule_id: str,
    outcome: str = "passed",
    **changes: object,
) -> owner.UnifiedAdmissionRuleEvaluation:
    values: dict[str, object] = {
        "schema_version": owner.RESULT_SCHEMA_VERSION,
        "admission_rule_id": rule_id,
        "admission_rule_name": exact15.RULE_NAMES.get(rule_id, "unknown_rule"),
        "outcome": outcome,
        "passed": outcome == "passed",
        "blocks_candidate": outcome != "passed",
        "reason": "" if outcome == "passed" else f"SYNTHETIC_{outcome.upper()}",
        "normalized_values": (),
        "validated_candidate_fields": (),
        "consumed_candidate_fields": (),
        "consumed_context_items": (),
        "evaluator_io_used": False,
        "adapter_id": exact15.ADAPTER_IDS.get(rule_id, "unknown_adapter"),
    }
    values.update(changes)
    return owner.UnifiedAdmissionRuleEvaluation(**values)


def vector(scope: str) -> tuple[owner.UnifiedAdmissionRuleEvaluation, ...]:
    return tuple(evaluation(rule_id) for rule_id in REQUIRED[scope])


def replace_item(
    values: tuple[object, ...], index: int, value: object
) -> tuple[object, ...]:
    if index < 0:
        index += len(values)
    return values[:index] + (value,) + values[index + 1 :]


def forged(
    source: owner.UnifiedAdmissionRuleEvaluation,
    **changes: object,
) -> owner.UnifiedAdmissionRuleEvaluation:
    values = dict(vars(source))
    values.update(changes)
    item = object.__new__(owner.UnifiedAdmissionRuleEvaluation)
    for name, value in values.items():
        object.__setattr__(item, name, value)
    return item


def verdict(scope: str = SCOPES[0]) -> production.CombinedAdmissionCandidateVerdict:
    return production.aggregate_admission_rule_evaluations(
        scope, ordered_rule_evaluations=vector(scope)
    )


def test_public_api_exact_signature_and_exports() -> None:
    assert production.__all__ == (
        "CombinedAdmissionCandidateVerdict",
        "aggregate_admission_rule_evaluations",
    )
    signature = inspect.signature(production.aggregate_admission_rule_evaluations)
    parameters = tuple(signature.parameters.values())
    assert tuple(parameter.name for parameter in parameters) == (
        "scope_id",
        "ordered_rule_evaluations",
    )
    assert parameters[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameters[1].kind is inspect.Parameter.KEYWORD_ONLY
    assert all(parameter.default is inspect.Parameter.empty for parameter in parameters)
    assert parameters[0].annotation == "str"
    assert parameters[1].annotation == (
        "tuple[UnifiedAdmissionRuleEvaluation, ...]"
    )
    assert signature.return_annotation == "CombinedAdmissionCandidateVerdict"


def test_result_exact13_frozen_vars_types_and_reconstruction() -> None:
    result = verdict()
    assert dataclasses.is_dataclass(result)
    assert result.__dataclass_params__.frozen
    assert tuple(field.name for field in dataclasses.fields(result)) == FIELDS
    assert tuple(vars(result)) == FIELDS
    assert type(vars(result)) is dict
    assert type(result.schema_version) is str
    assert type(result.scope_id) is str
    assert type(result.outcome) is str
    assert type(result.passed) is bool
    assert type(result.blocks_scope_action) is bool
    assert type(result.reason) is str
    assert all(type(vars(result)[name]) is tuple for name in FIELDS[6:12])
    assert type(result.aggregation_io_used) is bool
    assert type(result)(**vars(result)) == result
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.outcome = "invalid"  # type: ignore[misc]


def test_actual_runtime_type_and_vocabularies() -> None:
    assert exact15.UnifiedAdmissionRuleEvaluation is owner.UnifiedAdmissionRuleEvaluation
    assert production.UnifiedAdmissionRuleEvaluation is owner.UnifiedAdmissionRuleEvaluation
    assert owner.OUTCOME_VOCABULARY == ("passed", "blocked", "invalid", "rejected")
    assert production.AGGREGATION_OUTCOME_VOCABULARY == (
        "passed",
        "blocked",
        "invalid",
    )
    assert production.REASON_VOCABULARY == (
        "COMBINED_ADMISSION_SCOPE_ID_INVALID",
        "COMBINED_ADMISSION_RULE_EVALUATION_VECTOR_TYPE_INVALID",
        "COMBINED_ADMISSION_RULE_EVALUATION_INVARIANT_INVALID",
        "COMBINED_ADMISSION_RULE_MEMBERSHIP_INVALID",
        "COMBINED_ADMISSION_REQUIRED_RULE_INVALID",
        "COMBINED_ADMISSION_REQUIRED_RULE_BLOCKED",
    )


def test_exact4_memberships_and_b3_contract() -> None:
    assert SCOPES == (
        "download_execution_permission",
        "post_download_acceptance_permission",
        "pre_final_split_acceptance_permission",
        "training_execution_admission_permission",
    )
    assert tuple(map(len, REQUIRED.values())) == (11, 13, 14, 15)
    assert ("scaffold_only", "B3") in (
        ("warhead_only", "A"),
        ("linker_plus_warhead", "B"),
        ("scaffold_plus_warhead", "B2"),
        ("scaffold_only", "B3"),
        ("scaffold_plus_linker_plus_warhead", "C"),
    )


@pytest.mark.parametrize("scope", [None, True, 7, "", "unknown"])
def test_scope_invalid_projection(scope: object) -> None:
    result = production.aggregate_admission_rule_evaluations(
        scope, ordered_rule_evaluations=()  # type: ignore[arg-type]
    )
    assert result.outcome == "invalid"
    assert result.reason == production.SCOPE_ID_INVALID_REASON
    assert result.scope_id == (scope if type(scope) is str else "")
    assert result.required_rule_ids == ()
    assert result.evaluated_rule_ids == ()
    assert result.rule_evaluations == ()
    assert result.invalid_rule_ids == ()
    assert result.blocked_rule_ids == ()
    assert result.failing_rule_ids == ()


@pytest.mark.parametrize("invalid_vector", [None, [], {}, "x", True])
def test_vector_type_invalid_projection(invalid_vector: object) -> None:
    scope = SCOPES[0]
    result = production.aggregate_admission_rule_evaluations(
        scope, ordered_rule_evaluations=invalid_vector  # type: ignore[arg-type]
    )
    assert result.reason == production.VECTOR_TYPE_INVALID_REASON
    assert result.required_rule_ids == REQUIRED[scope]
    assert not result.evaluated_rule_ids
    assert not result.rule_evaluations


@pytest.mark.parametrize(
    ("scope", "index", "rule_id"),
    [
        (scope, index, rule_id)
        for scope in SCOPES
        for index, rule_id in enumerate(REQUIRED[scope])
    ],
)
def test_every_required_rule_blocked(scope: str, index: int, rule_id: str) -> None:
    values = vector(scope)
    changed = replace_item(values, index, evaluation(rule_id, "blocked"))
    result = production.aggregate_admission_rule_evaluations(
        scope, ordered_rule_evaluations=changed
    )
    assert result.outcome == "blocked"
    assert result.reason == production.REQUIRED_RULE_BLOCKED_REASON
    assert result.blocked_rule_ids == (rule_id,)
    assert result.failing_rule_ids == (rule_id,)
    assert result.rule_evaluations is changed


@pytest.mark.parametrize(
    ("scope", "index", "rule_id"),
    [
        (scope, index, rule_id)
        for scope in SCOPES
        for index, rule_id in enumerate(REQUIRED[scope])
    ],
)
def test_every_required_rule_invalid(scope: str, index: int, rule_id: str) -> None:
    values = vector(scope)
    changed = replace_item(values, index, evaluation(rule_id, "invalid"))
    result = production.aggregate_admission_rule_evaluations(
        scope, ordered_rule_evaluations=changed
    )
    assert result.outcome == "invalid"
    assert result.reason == production.REQUIRED_RULE_INVALID_REASON
    assert result.invalid_rule_ids == (rule_id,)
    assert result.failing_rule_ids == (rule_id,)
    assert result.rule_evaluations is changed


@pytest.mark.parametrize("scope", SCOPES)
def test_full_vector_multi_invalid_blocked_and_failing(scope: str) -> None:
    values = vector(scope)
    values = replace_item(
        values, 0, evaluation(REQUIRED[scope][0], "blocked")
    )
    values = replace_item(
        values, 1, evaluation(REQUIRED[scope][1], "invalid")
    )
    values = replace_item(
        values, -1, evaluation(REQUIRED[scope][-1], "blocked")
    )
    result = production.aggregate_admission_rule_evaluations(
        scope, ordered_rule_evaluations=values
    )
    assert result.outcome == "invalid"
    assert result.invalid_rule_ids == (REQUIRED[scope][1],)
    assert result.blocked_rule_ids == (
        REQUIRED[scope][0],
        REQUIRED[scope][-1],
    )
    assert result.failing_rule_ids == (
        REQUIRED[scope][0],
        REQUIRED[scope][1],
        REQUIRED[scope][-1],
    )


@pytest.mark.parametrize("scope", SCOPES)
def test_all_invalid_and_all_blocked_are_fully_collected(scope: str) -> None:
    invalid = tuple(evaluation(rule, "invalid") for rule in REQUIRED[scope])
    invalid_result = production.aggregate_admission_rule_evaluations(
        scope, ordered_rule_evaluations=invalid
    )
    assert invalid_result.invalid_rule_ids == REQUIRED[scope]
    assert invalid_result.failing_rule_ids == REQUIRED[scope]
    blocked = tuple(evaluation(rule, "blocked") for rule in REQUIRED[scope])
    blocked_result = production.aggregate_admission_rule_evaluations(
        scope, ordered_rule_evaluations=blocked
    )
    assert blocked_result.blocked_rule_ids == REQUIRED[scope]
    assert blocked_result.failing_rule_ids == REQUIRED[scope]


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("position", ["first", "middle", "last"])
def test_missing_first_middle_last(scope: str, position: str) -> None:
    values = vector(scope)
    index = {"first": 0, "middle": len(values) // 2, "last": len(values) - 1}[position]
    changed = values[:index] + values[index + 1 :]
    result = production.aggregate_admission_rule_evaluations(
        scope, ordered_rule_evaluations=changed
    )
    assert result.reason == production.MEMBERSHIP_INVALID_REASON
    assert result.evaluated_rule_ids == tuple(
        item.admission_rule_id for item in changed
    )
    assert result.rule_evaluations == ()


@pytest.mark.parametrize("scope", SCOPES)
def test_extra_duplicate_reorder_unknown_and_external(scope: str) -> None:
    values = vector(scope)
    external = next(
        (rule for rule in production.RULE_IDS if rule not in REQUIRED[scope]),
        "ADMIT_999",
    )
    cases = (
        values + (evaluation(external),),
        values + (values[0],),
        (values[1], values[0]) + values[2:],
        values[:-1] + (evaluation("ADMIT_999"),),
        values[:-1] + (evaluation(external),),
    )
    for changed in cases:
        result = production.aggregate_admission_rule_evaluations(
            scope, ordered_rule_evaluations=changed
        )
        assert result.reason == production.MEMBERSHIP_INVALID_REASON
        assert result.evaluated_rule_ids == tuple(
            item.admission_rule_id for item in changed
        )
        assert not result.rule_evaluations


class ChildSubclass(owner.UnifiedAdmissionRuleEvaluation):
    pass


def test_wrong_child_and_subclass_rejected_without_retention() -> None:
    scope = SCOPES[0]
    values = vector(scope)
    subclass = ChildSubclass(**vars(values[0]))
    for item in (object(), subclass):
        changed = replace_item(values, 0, item)
        result = production.aggregate_admission_rule_evaluations(
            scope, ordered_rule_evaluations=changed
        )
        assert result.reason == production.EVALUATION_INVARIANT_INVALID_REASON
        assert not result.evaluated_rule_ids
        assert not result.rule_evaluations


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        ("schema_version", 7),
        ("admission_rule_id", 7),
        ("admission_rule_name", 7),
        ("outcome", 7),
        ("passed", 0),
        ("blocks_candidate", 0),
        ("reason", 7),
        ("normalized_values", []),
        ("validated_candidate_fields", []),
        ("consumed_candidate_fields", []),
        ("consumed_context_items", []),
        ("evaluator_io_used", True),
        ("adapter_id", 7),
    ],
)
def test_forged_exact13_field_mutations_fail_closed(
    field_name: str, replacement: object
) -> None:
    scope = SCOPES[0]
    values = vector(scope)
    bad = forged(values[0], **{field_name: replacement})
    result = production.aggregate_admission_rule_evaluations(
        scope, ordered_rule_evaluations=replace_item(values, 0, bad)
    )
    assert result.reason == production.EVALUATION_INVARIANT_INVALID_REASON
    assert not result.rule_evaluations


def test_rejected_is_runtime_valid_but_aggregation_inadmissible() -> None:
    scope = SCOPES[0]
    values = vector(scope)
    rejected = evaluation(REQUIRED[scope][0], "rejected")
    assert production._runtime_structure_valid(rejected)
    assert not production._aggregation_identity_and_outcome_admissible(rejected)
    result = production.aggregate_admission_rule_evaluations(
        scope, ordered_rule_evaluations=replace_item(values, 0, rejected)
    )
    assert result.reason == production.EVALUATION_INVARIANT_INVALID_REASON
    assert not result.rule_evaluations


def test_known_name_and_adapter_drift_fail_closed_unknown_identity_reaches_membership() -> None:
    scope = SCOPES[0]
    values = vector(scope)
    for change in (
        {"admission_rule_name": "wrong"},
        {"adapter_id": "wrong"},
    ):
        bad = forged(values[0], **change)
        result = production.aggregate_admission_rule_evaluations(
            scope, ordered_rule_evaluations=replace_item(values, 0, bad)
        )
        assert result.reason == production.EVALUATION_INVARIANT_INVALID_REASON
    unknown = evaluation("ADMIT_999")
    result = production.aggregate_admission_rule_evaluations(
        scope, ordered_rule_evaluations=replace_item(values, 0, unknown)
    )
    assert result.reason == production.MEMBERSHIP_INVALID_REASON


def test_nested_duplicates_are_accepted_uninterpreted_and_unchanged() -> None:
    scope = SCOPES[0]
    values = vector(scope)
    duplicate = evaluation(
        REQUIRED[scope][0],
        normalized_values=(("a", "1"), ("a", "2")),
        validated_candidate_fields=(("b", "1"), ("b", "2")),
        consumed_candidate_fields=("c", "c"),
        consumed_context_items=("d", "d"),
    )
    changed = replace_item(values, 0, duplicate)
    before = tuple(dict(vars(item)) for item in changed)
    result = production.aggregate_admission_rule_evaluations(
        scope, ordered_rule_evaluations=changed
    )
    assert result.outcome == "passed"
    assert result.rule_evaluations is changed
    assert tuple(dict(vars(item)) for item in changed) == before


def test_valid_tuple_identity_determinism_and_no_permission_mutation() -> None:
    scope = SCOPES[-1]
    values = vector(scope)
    first = production.aggregate_admission_rule_evaluations(
        scope, ordered_rule_evaluations=values
    )
    second = production.aggregate_admission_rule_evaluations(
        scope, ordered_rule_evaluations=values
    )
    assert first == second
    assert first.rule_evaluations is values
    assert first.aggregation_io_used is False
    assert production.CURRENT_PERMISSION is False
    assert production.AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT == 0


def test_full_structure_scan_does_not_short_circuit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scope = SCOPES[0]
    values = vector(scope)
    original = production._runtime_structure_valid
    visited: list[str] = []

    def instrumented(item: object) -> bool:
        visited.append(getattr(item, "admission_rule_id", "<unknown>"))
        return False if len(visited) == 1 else original(item)

    monkeypatch.setattr(production, "_runtime_structure_valid", instrumented)
    result = production.aggregate_admission_rule_evaluations(
        scope, ordered_rule_evaluations=values
    )
    assert result.reason == production.EVALUATION_INVARIANT_INVALID_REASON
    assert visited == list(REQUIRED[scope])


def test_full_admissibility_scan_does_not_short_circuit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scope = SCOPES[0]
    values = vector(scope)
    original = production._aggregation_identity_and_outcome_admissible
    visited: list[str] = []

    def instrumented(item: owner.UnifiedAdmissionRuleEvaluation) -> bool:
        visited.append(item.admission_rule_id)
        return False if len(visited) == 1 else original(item)

    monkeypatch.setattr(
        production,
        "_aggregation_identity_and_outcome_admissible",
        instrumented,
    )
    result = production.aggregate_admission_rule_evaluations(
        scope, ordered_rule_evaluations=values
    )
    assert result.reason == production.EVALUATION_INVARIANT_INVALID_REASON
    assert visited == list(REQUIRED[scope])


def test_full_outcome_scan_collects_after_first_failure() -> None:
    scope = SCOPES[0]
    values = tuple(
        evaluation(
            rule,
            "invalid" if index == 0 else "blocked" if index % 2 else "passed",
        )
        for index, rule in enumerate(REQUIRED[scope])
    )
    result = production.aggregate_admission_rule_evaluations(
        scope, ordered_rule_evaluations=values
    )
    assert result.invalid_rule_ids == (REQUIRED[scope][0],)
    assert result.blocked_rule_ids == REQUIRED[scope][1::2]
    assert result.failing_rule_ids == (
        REQUIRED[scope][0],
        *REQUIRED[scope][1::2],
    )


def test_public_runtime_has_no_io_dispatch_or_handler_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scope = SCOPES[0]
    vectors = [
        vector(scope),
        replace_item(vector(scope), 0, evaluation(REQUIRED[scope][0], "blocked")),
        replace_item(vector(scope), 0, evaluation(REQUIRED[scope][0], "invalid")),
        replace_item(vector(scope), 0, evaluation(REQUIRED[scope][0], "rejected")),
        vector(scope)[:-1],
    ]

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("forbidden runtime side effect")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(os, "open", forbidden)
    monkeypatch.setattr(os, "stat", forbidden)
    monkeypatch.setattr(os, "lstat", forbidden)
    monkeypatch.setattr(os, "listdir", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "check_output", forbidden)
    monkeypatch.setattr(exact15, "evaluate_admission_rule", forbidden)
    for callable_value in exact15.EVALUATOR_REGISTRY.values():
        monkeypatch.setattr(
            importlib_module := __import__(
                callable_value.__module__, fromlist=[callable_value.__name__]
            ),
            callable_value.__name__,
            forbidden,
        )
        assert importlib_module is not None
    assert [
        production.aggregate_admission_rule_evaluations(
            scope, ordered_rule_evaluations=values
        ).reason
        for values in vectors
    ] == [
        "",
        production.REQUIRED_RULE_BLOCKED_REASON,
        production.REQUIRED_RULE_INVALID_REASON,
        production.EVALUATION_INVARIANT_INVALID_REASON,
        production.MEMBERSHIP_INVALID_REASON,
    ]


def test_public_source_boundary_has_no_dispatch_handler_or_io_call() -> None:
    source = (ROOT / production.SUPPORT_PATHS[0]).read_text()
    runtime_source = source.split(
        "# Explicit evidence-builder and materializer boundary.", 1
    )[0]
    assert "evaluate_admission_rule(" not in runtime_source
    assert "EVALUATOR_REGISTRY" not in runtime_source
    assert "candidate_record" not in runtime_source
    assert "import torch" not in runtime_source
    assert "subprocess." not in runtime_source
    assert "open(" not in runtime_source


@pytest.mark.parametrize(
    "changes",
    [
        {"schema_version": "wrong"},
        {"scope_id": 1},
        {"outcome": "unknown"},
        {"passed": 1},
        {"blocks_scope_action": 0},
        {"reason": "x"},
        {"required_rule_ids": []},
        {"evaluated_rule_ids": []},
        {"rule_evaluations": []},
        {"invalid_rule_ids": []},
        {"blocked_rule_ids": []},
        {"failing_rule_ids": []},
        {"aggregation_io_used": True},
    ],
)
def test_direct_result_construction_field_and_common_invariants(
    changes: dict[str, object],
) -> None:
    values = dict(vars(verdict()))
    values.update(changes)
    with pytest.raises((TypeError, ValueError)):
        production.CombinedAdmissionCandidateVerdict(**values)


def test_direct_result_reason_specific_negative_matrix() -> None:
    passed = dict(vars(verdict()))
    scope = SCOPES[0]
    cases = []
    cases.append({**passed, "reason": "nonempty"})
    cases.append(
        {
            **passed,
            "outcome": "blocked",
            "passed": False,
            "blocks_scope_action": True,
            "reason": production.REQUIRED_RULE_INVALID_REASON,
        }
    )
    cases.append(
        {
            **passed,
            "outcome": "invalid",
            "passed": False,
            "blocks_scope_action": True,
            "reason": production.REQUIRED_RULE_BLOCKED_REASON,
        }
    )
    invalid_scope = dict(
        vars(
            production.aggregate_admission_rule_evaluations(
                "unknown", ordered_rule_evaluations=()
            )
        )
    )
    cases.append({**invalid_scope, "required_rule_ids": REQUIRED[scope]})
    vector_invalid = dict(
        vars(
            production.aggregate_admission_rule_evaluations(
                scope, ordered_rule_evaluations=[]  # type: ignore[arg-type]
            )
        )
    )
    cases.append({**vector_invalid, "evaluated_rule_ids": ("ADMIT_001",)})
    invariant = dict(
        vars(
            production.aggregate_admission_rule_evaluations(
                scope, ordered_rule_evaluations=(object(),)  # type: ignore[arg-type]
            )
        )
    )
    cases.append({**invariant, "rule_evaluations": vector(scope)})
    membership = dict(
        vars(
            production.aggregate_admission_rule_evaluations(
                scope, ordered_rule_evaluations=vector(scope)[:-1]
            )
        )
    )
    cases.append({**membership, "evaluated_rule_ids": REQUIRED[scope]})
    for values in cases:
        with pytest.raises((TypeError, ValueError)):
            production.CombinedAdmissionCandidateVerdict(**values)


def test_source_snapshot_exact13_and_artifact_counts() -> None:
    snapshot = production.build_frozen_source_snapshot(ROOT)
    assert len(snapshot) == 13
    assert tuple(item.relative_path for item in snapshot) == production.SOURCE_PATHS
    assert all(item.index_stage == 0 for item in snapshot)
    artifacts = production.build_artifacts(snapshot, repo_root=ROOT)
    assert tuple(artifacts) == production.OUTPUT_FILES
    assert len(checker._csv(artifacts[production.RUNTIME_CONTRACT_FILENAME])) == 49
    truth = checker._csv(artifacts[production.TRUTH_FILENAME])
    assert len(truth) == 201
    assert len({row["case_group"] for row in truth}) == 23
    assert all(row["case_passed"] == "true" for row in truth)
    assert len(checker._csv(artifacts[production.SAFETY_FILENAME])) == 30
    preconditions = checker._csv(artifacts[production.PRECONDITION_FILENAME])
    assert len(preconditions) == 45
    assert [
        row["precondition_id"]
        for row in preconditions
        if row["transition_action"] != "unchanged"
    ] == ["PRE_036"]


def test_source_snapshot_content_tamper_fails_closed() -> None:
    snapshot = production.build_frozen_source_snapshot(ROOT)
    changed = list(snapshot)
    changed[0] = dataclasses.replace(changed[0], content=changed[0].content + b"x")
    with pytest.raises(ValueError, match="source snapshot record invariant drift"):
        production.build_artifacts(tuple(changed), repo_root=ROOT)


def test_duplicate_json_key_rejected() -> None:
    with pytest.raises(ValueError, match="unique keys"):
        production._json(b'{"a":1,"a":2}')
    with pytest.raises(ValueError, match="unique keys"):
        checker._json(b'{"a":1,"a":2}')


def test_parent_chain_reader_rejects_symlink(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (real / "leaf").write_bytes(b"x")
    (tmp_path / "link").symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="component unsafe"):
        production._pinned_regular_read(tmp_path, Path("link/leaf"))
    with pytest.raises(ValueError, match="component unsafe"):
        checker._pinned_read(tmp_path, Path("link/leaf"))


def test_materializer_gpfs_einval_fails_closed_and_retains_authenticated_stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = production.build_frozen_source_snapshot(ROOT)
    payloads = production.build_artifacts(snapshot, repo_root=ROOT)

    def einval(*args: object) -> int:
        ctypes.set_errno(22)
        return -1

    monkeypatch.setattr(production, "_RENAMEAT2", einval)
    output = tmp_path / production.STAGE
    with pytest.raises(production.MaterializationRetentionError) as captured:
        production._materialize(output, payloads, repo_root=ROOT)
    retained = captured.value.authenticated_retained_path
    assert retained is not None
    assert retained.is_dir()
    assert retained.name.startswith(production.STAGING_NAME_PREFIX)
    assert production._read_output_set(retained) == payloads
    assert not output.exists()


def test_pre36_issue_readiness_and_feature_blocker_continuity() -> None:
    manifest = checker._json(
        (ROOT / production.DEFAULT_OUTPUT_ROOT / production.MANIFEST_FILENAME).read_bytes()
    )
    assert manifest["precondition_transition"] == {
        "complete_count": 43,
        "implementation_blocking_count": 2,
        "incomplete_count": 2,
        "remaining_open_precondition_ids": ["PRE_038", "PRE_042"],
        "row_count": 45,
        "supported_but_not_frozen_count": 0,
        "transition_count": 1,
        "transition_ids": ["PRE_036"],
    }
    assert manifest["issue_continuity"]["transition_count"] == 0
    assert manifest["readiness"]["combined_candidate_verdict_implemented"] is True
    assert manifest["readiness"]["cross_rule_aggregation_implemented"] is True
    assert manifest["readiness"]["feature_semantics_audit_completed"] is False
    assert manifest["readiness"]["ready_for_training"] is False
    assert "UNKNOWN_ATOM_FEATURE_POLICY" in manifest["feature_semantics_warning"]
    assert manifest["canonical_masks"][3] == {
        "semantic_name": "scaffold_only",
        "alias": "B3",
    }


def test_issue_inventory_exact30_byte_identical() -> None:
    output = ROOT / production.DEFAULT_OUTPUT_ROOT / production.ISSUE_FILENAME
    source = (
        ROOT
        / "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_contract_v1/"
        "covapie_combined_candidate_verdict_issue_readiness_inventory.csv"
    )
    assert output.read_bytes() == source.read_bytes()
    assert production._sha(output.read_bytes()) == (
        "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7"
    )


def test_production_checker_disk_and_new_materialization_equality(
    tmp_path: Path,
) -> None:
    local_snapshot = checker._source_snapshot()
    candidate_snapshot = production.build_frozen_source_snapshot(ROOT)
    local = checker._expected_artifacts(production, local_snapshot)
    actual = production.build_artifacts(candidate_snapshot, repo_root=ROOT)
    disk = {
        name: (ROOT / production.DEFAULT_OUTPUT_ROOT / name).read_bytes()
        for name in production.OUTPUT_FILES
    }
    assert actual == local == disk
    output = tmp_path / production.STAGE
    production.run_covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1(
        output, repo_root=ROOT
    )
    assert production._read_output_set(output) == local
    before = os.lstat(output)
    production.run_covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1(
        output, repo_root=ROOT
    )
    after = os.lstat(output)
    assert (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)


def test_manifest_hash_truth_and_no_self_hash() -> None:
    manifest_path = ROOT / production.DEFAULT_OUTPUT_ROOT / production.MANIFEST_FILENAME
    manifest = checker._json(manifest_path.read_bytes())
    assert manifest["exact10_file_count"] == 10
    assert tuple(manifest["exact10_files"]) == tuple(
        path.as_posix() for path in production.EXACT10
    )
    assert manifest["manifest_self_sha256_recorded"] is False
    assert production.MANIFEST_FILENAME not in {
        Path(path).name for path in manifest["derived_output_sha256"]
    }
    for path, digest in manifest["derived_output_sha256"].items():
        assert production._sha((ROOT / path).read_bytes()) == digest
    for path, digest in manifest["support_file_sha256"].items():
        assert production._sha((ROOT / path).read_bytes()) == digest


def test_checker_independent_local_oracle_and_no_candidate_expected_alias() -> None:
    source = CHECKER_PATH.read_text()
    assert "def _local_aggregate" in source
    assert "def _expected_artifacts" in source
    assert "candidate.build_artifacts(actual_snapshot" in source
    assert "actual != expected" in source
    assert "candidate._runtime_contract_rows" not in source
    assert "candidate._implementation_truth_rows" not in source
    assert "git\", \"write-tree\"" not in source


def test_lifecycle_precommit_or_detached_candidate() -> None:
    first = checker.verify_lifecycle()
    second = checker.verify_lifecycle()
    assert first == second
    assert first.lifecycle in {"pre_commit", "post_commit"}
    assert first.exact10 == tuple(path.as_posix() for path in production.EXACT10)
    assert len(first.recursive_inventory) == 11
    assert first.derived_roots == (production.DEFAULT_OUTPUT_ROOT.as_posix(),)
    assert first.refs == checker._ref_inventory(ROOT)
    assert any(
        record.refname == "refs/heads/main"
        and record.objecttype == "commit"
        for record in first.refs
    )


@pytest.mark.parametrize(
    "refname",
    (
        "refs/covapie-review-residue/synthetic",
        "refs/original/covapie-synthetic",
        "refs/stash",
        "refs/remotes/origin/covapie-temp",
        "refs/codex/covapie-temp",
    ),
)
def test_unexpected_persistent_ref_namespaces_rejected(
    tmp_path: Path,
    refname: str,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    git(root, "update-ref", refname, base)
    inventory = checker._ref_inventory(root)
    assert refname in {record.refname for record in inventory}
    with pytest.raises(ValueError, match="persistent ref namespace"):
        checker.verify_lifecycle(root, base=base)


def test_platform_turn_diffs_ref_allowed_and_stable(
    tmp_path: Path,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    refname = valid_platform_capture_ref()
    tree = git(root, "rev-parse", "HEAD^{tree}").decode().strip()
    git(root, "update-ref", refname, tree)
    before = checker._ref_inventory(root)
    first = checker.verify_lifecycle(root, base=base)
    second = checker.verify_lifecycle(root, base=base)
    after = checker._ref_inventory(root)
    assert before == first.refs == second.refs == after
    assert checker.RefRecord(refname, tree, "tree") in first.refs


@pytest.mark.parametrize("object_kind", ("commit", "blob", "tag"))
def test_valid_platform_refname_non_tree_object_rejected(
    tmp_path: Path,
    object_kind: str,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    if object_kind == "commit":
        objectname = base
    elif object_kind == "blob":
        objectname = git(
            root,
            "rev-parse",
            "HEAD:data/raw/historical-00.txt",
        ).decode().strip()
    else:
        tag_payload = (
            f"object {base}\n"
            "type commit\n"
            "tag synthetic-platform-object\n"
            "tagger CovaPIE Test <covapie-test@example.invalid> 0 +0000\n"
            "\n"
            "synthetic platform tag object\n"
        ).encode()
        objectname = git_with_input(root, tag_payload, "mktag").decode().strip()
    git(root, "update-ref", valid_platform_capture_ref(), objectname)
    with pytest.raises(ValueError, match="platform ref object type"):
        checker.verify_lifecycle(root, base=base)


@pytest.mark.parametrize("object_kind", ("commit", "tree"))
def test_covapie_disguised_platform_ref_rejected(
    tmp_path: Path,
    object_kind: str,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    objectname = (
        base
        if object_kind == "commit"
        else git(root, "rev-parse", "HEAD^{tree}").decode().strip()
    )
    refname = f"{checker.PLATFORM_REF_NAMESPACE}/covapie-temp"
    git(root, "update-ref", refname, objectname)
    with pytest.raises(ValueError, match="platform ref"):
        checker.verify_lifecycle(root, base=base)


@pytest.mark.parametrize("suffix", ("", "-tree-residue"))
def test_stage_named_platform_tree_ref_rejected(
    tmp_path: Path,
    suffix: str,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    tree = git(root, "rev-parse", "HEAD^{tree}").decode().strip()
    refname = (
        f"{checker.PLATFORM_REF_NAMESPACE}/{checker.STAGE}{suffix}"
    )
    git(root, "update-ref", refname, tree)
    with pytest.raises(ValueError, match="platform ref"):
        checker.verify_lifecycle(root, base=base)


@pytest.mark.parametrize(
    "suffix",
    ("tmp", "backup", "review", "candidate", "temporary"),
)
def test_unmanaged_platform_suffix_rejected(
    tmp_path: Path,
    suffix: str,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    tree = git(root, "rev-parse", "HEAD^{tree}").decode().strip()
    git(
        root,
        "update-ref",
        f"{checker.PLATFORM_REF_NAMESPACE}/{suffix}",
        tree,
    )
    with pytest.raises(ValueError, match="platform ref"):
        checker.verify_lifecycle(root, base=base)


def test_current_platform_refs_match_strict_tree_grammar_and_are_stable() -> None:
    before = checker._ref_inventory(ROOT)
    platform = tuple(
        record
        for record in before
        if checker._is_platform_namespace_ref(record.refname)
    )
    assert platform
    assert all(checker._is_platform_ref(record.refname) for record in platform)
    assert all(record.objecttype == "tree" for record in platform)
    checker.verify_lifecycle()
    assert checker._ref_inventory(ROOT) == before


def test_optional_origin_main_and_symbolic_head_allowed(
    tmp_path: Path,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    git(root, "update-ref", "refs/remotes/origin/main", base)
    git(
        root,
        "symbolic-ref",
        "refs/remotes/origin/HEAD",
        "refs/remotes/origin/main",
    )
    state = checker.verify_lifecycle(root, base=base)
    records = {record.refname: record for record in state.refs}
    assert records["refs/remotes/origin/main"] == checker.RefRecord(
        "refs/remotes/origin/main", base, "commit"
    )
    assert records["refs/remotes/origin/HEAD"] == checker.RefRecord(
        "refs/remotes/origin/HEAD", base, "commit"
    )


def test_optional_origin_main_allowed_without_origin_head(
    tmp_path: Path,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    git(root, "update-ref", "refs/remotes/origin/main", base)
    state = checker.verify_lifecycle(root, base=base)
    assert checker.RefRecord(
        "refs/remotes/origin/main", base, "commit"
    ) in state.refs
    assert all(
        record.refname != "refs/remotes/origin/HEAD"
        for record in state.refs
    )


def test_precommit_origin_main_other_target_rejected(
    tmp_path: Path,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    other = synthetic_other_commit(root, base)
    git(root, "update-ref", "refs/remotes/origin/main", other)
    with pytest.raises(ValueError, match="pre-commit topology"):
        checker.verify_lifecycle(root, base=base)


def test_origin_head_target_must_match_origin_main(
    tmp_path: Path,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    other = synthetic_other_commit(root, base)
    git(root, "update-ref", "refs/remotes/origin/main", base)
    git(root, "update-ref", "refs/remotes/origin/HEAD", other)
    with pytest.raises(ValueError, match="origin HEAD/main target"):
        checker.verify_lifecycle(root, base=base)


def test_custom_ref_added_midscan_rejected(tmp_path: Path) -> None:
    root, base = synthetic_precommit(tmp_path)
    changed = False

    def add_ref(event: str, path: Path) -> None:
        nonlocal changed
        if event == "after_repository_root_open" and not changed:
            changed = True
            git(
                root,
                "update-ref",
                "refs/covapie-midscan/synthetic",
                base,
            )

    with pytest.raises(ValueError, match="persistent ref namespace"):
        checker.verify_lifecycle(root, base=base, hook=add_ref)


def test_origin_main_repointed_midscan_rejected(tmp_path: Path) -> None:
    root, base = synthetic_precommit(tmp_path)
    other = synthetic_other_commit(root, base)
    git(root, "update-ref", "refs/remotes/origin/main", base)
    changed = False

    def repoint_remote(event: str, path: Path) -> None:
        nonlocal changed
        if event == "after_repository_root_open" and not changed:
            changed = True
            git(root, "update-ref", "refs/remotes/origin/main", other)

    with pytest.raises(ValueError, match="topology|drift"):
        checker.verify_lifecycle(root, base=base, hook=repoint_remote)


@pytest.mark.parametrize("mutation", ("repoint", "delete"))
def test_platform_ref_midscan_mutation_rejected(
    tmp_path: Path,
    mutation: str,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    refname = valid_platform_capture_ref()
    tree = git(root, "rev-parse", "HEAD^{tree}").decode().strip()
    git(root, "update-ref", refname, tree)
    replacement = git_with_input(root, b"", "mktree").decode().strip()
    assert replacement != tree
    changed = False

    def mutate_ref(event: str, path: Path) -> None:
        nonlocal changed
        if event != "after_repository_root_open" or changed:
            return
        changed = True
        if mutation == "repoint":
            git(root, "update-ref", refname, replacement)
        else:
            git(root, "update-ref", "-d", refname)

    with pytest.raises(ValueError, match="drift"):
        checker.verify_lifecycle(root, base=base, hook=mutate_ref)


def test_after_candidate_validation_custom_ref_rejected(
    tmp_path: Path,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    refname = "refs/covapie-after-candidate/synthetic"

    def add_ref() -> None:
        git(root, "update-ref", refname, base)

    with pytest.raises(ValueError, match="persistent ref namespace"):
        checker._verify_complete_checker_run(
            after_candidate_validation=add_ref,
            lifecycle_root=root,
            lifecycle_base=base,
        )


def test_after_candidate_validation_origin_main_repoint_rejected(
    tmp_path: Path,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    other = synthetic_other_commit(root, base)
    git(root, "update-ref", "refs/remotes/origin/main", base)

    def repoint_remote() -> None:
        git(root, "update-ref", "refs/remotes/origin/main", other)

    with pytest.raises(ValueError, match="topology"):
        checker._verify_complete_checker_run(
            after_candidate_validation=repoint_remote,
            lifecycle_root=root,
            lifecycle_base=base,
        )


@pytest.mark.parametrize(
    "payload",
    (
        b"\xff\n",
        b"refs/heads/main\tdeadbeef\n",
        b"refs/heads/main\tdeadbeef\tcommit\n",
        b"refs/heads/main\t0000000000000000000000000000000000000000\t\n",
        (
            b"refs/heads/main\t0000000000000000000000000000000000000000"
            b"\tcommit\nrefs/heads/main\t1111111111111111111111111111111111111111"
            b"\tcommit\n"
        ),
    ),
)
def test_ref_inventory_malformed_output_rejected(
    monkeypatch: pytest.MonkeyPatch,
    payload: bytes,
) -> None:
    result = subprocess.CompletedProcess(
        args=("git", "for-each-ref"),
        returncode=0,
        stdout=payload,
        stderr=b"",
    )
    monkeypatch.setattr(checker, "_git_result", lambda *args: result)
    with pytest.raises(ValueError, match="ref inventory"):
        checker._ref_inventory(ROOT)


def test_ignored_extra_leaf_inside_derived_root_rejected(
    tmp_path: Path,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    extra = checker.DERIVED_ROOT / "ignored-extra-note.txt"
    (root / extra).write_bytes(b"ignored residue\n")
    ignore_path(root, extra)
    assert synthetic_untracked(root) == {
        path.as_posix() for path in checker.EXACT10
    }
    with pytest.raises(ValueError, match="ignored|Exact10"):
        checker.assert_exact10_recursive_inventory(root)
    with pytest.raises(ValueError, match="ignored|Exact10"):
        checker.verify_lifecycle(root, base=base)


def test_ignored_extra_directory_and_child_rejected(
    tmp_path: Path,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    directory = checker.DERIVED_ROOT / "ignored-extra-directory"
    child = directory / "arbitrary.txt"
    (root / directory).mkdir()
    (root / child).write_bytes(b"ignored nested residue\n")
    ignore_path(root, directory)
    assert synthetic_untracked(root) == {
        path.as_posix() for path in checker.EXACT10
    }
    with pytest.raises(ValueError, match="ignored|Exact10"):
        checker.verify_lifecycle(root, base=base)


def test_ignored_empty_derived_directory_rejected(
    tmp_path: Path,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    directory = checker.DERIVED_ROOT / "ignored-empty-directory"
    (root / directory).mkdir()
    ignore_path(root, directory)
    assert synthetic_untracked(root) == {
        path.as_posix() for path in checker.EXACT10
    }
    with pytest.raises(ValueError, match="ignored|unsafe|Exact10"):
        checker.verify_lifecycle(root, base=base)


def test_exact6_leaf_symlink_rejected_without_touching_target(
    tmp_path: Path,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    leaf = root / checker.DERIVED_ROOT / checker.OUTPUT_NAMES[0]
    external = tmp_path / "external-target"
    external.write_bytes(b"external sentinel\n")
    leaf.unlink()
    leaf.symlink_to(external)
    with pytest.raises(ValueError, match="symlink|unsafe"):
        checker.verify_lifecycle(root, base=base)
    assert external.read_bytes() == b"external sentinel\n"


def test_embedded_stage_support_directory_residue_rejected(
    tmp_path: Path,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    directory = Path("scripts") / f"embedded-{checker.STAGE}-residue"
    (root / directory).mkdir()
    (root / directory / "arbitrary.txt").write_bytes(b"residue\n")
    ignore_path(root, directory)
    assert synthetic_untracked(root) == {
        path.as_posix() for path in checker.EXACT10
    }
    with pytest.raises(ValueError, match="ignored|Exact10"):
        checker.verify_lifecycle(root, base=base)


def test_unrelated_ignored_regular_file_remains_allowed(
    tmp_path: Path,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    unrelated = Path("scripts/unrelated-ignored-note.txt")
    (root / unrelated).write_bytes(b"unrelated\n")
    ignore_path(root, unrelated)
    assert synthetic_untracked(root) == {
        path.as_posix() for path in checker.EXACT10
    }
    assert checker.verify_lifecycle(root, base=base).lifecycle == "pre_commit"


@pytest.mark.parametrize(
    "name",
    (
        f"{checker.STAGING_PREFIX}synthetic",
        f"{checker.LEGACY_STAGING_PREFIXES[0]}synthetic",
        f"{checker.LEGACY_STAGING_PREFIXES[1]}synthetic",
    ),
)
def test_current_and_legacy_derived_staging_rejected(
    tmp_path: Path,
    name: str,
) -> None:
    root, _ = synthetic_precommit(tmp_path)
    (root / checker.DERIVED_ROOT.parent / name).mkdir()
    with pytest.raises(ValueError, match="staging residue"):
        checker.assert_exact10_recursive_inventory(root)


def test_matching_derived_sibling_rejected(tmp_path: Path) -> None:
    root, _ = synthetic_precommit(tmp_path)
    sibling = root / checker.DERIVED_ROOT.parent / f"{checker.STAGE}-sibling"
    sibling.mkdir()
    with pytest.raises(ValueError, match="matching derived sibling"):
        checker.assert_exact10_recursive_inventory(root)


def test_repository_root_replacement_race_rejected(tmp_path: Path) -> None:
    root, _ = synthetic_precommit(tmp_path)
    moved = tmp_path / "repo-held"
    replaced = False

    def replace_root(event: str, path: Path) -> None:
        nonlocal replaced
        if event == "after_repository_root_open" and not replaced:
            replaced = True
            os.rename(root, moved)
            root.mkdir()

    try:
        with pytest.raises(ValueError, match="root.*drift"):
            checker.assert_exact10_recursive_inventory(root, hook=replace_root)
    finally:
        if replaced:
            root.rmdir()
            os.rename(moved, root)


def test_same_byte_leaf_inode_replacement_rejected(
    tmp_path: Path,
) -> None:
    root, _ = synthetic_precommit(tmp_path)
    leaf = root / checker.DERIVED_ROOT / checker.OUTPUT_NAMES[0]
    replacement = tmp_path / "same-bytes-replacement"
    replacement.write_bytes(leaf.read_bytes())
    replaced = False

    def replace_leaf(event: str, path: Path) -> None:
        nonlocal replaced
        if (
            event == "before_directory_final_validation"
            and path == checker.DERIVED_ROOT
            and not replaced
        ):
            replaced = True
            os.replace(replacement, leaf)

    with pytest.raises(ValueError, match="drift"):
        checker.assert_exact10_recursive_inventory(root, hook=replace_leaf)


def test_formal_main_single_worktree_postcommit_is_valid(
    tmp_path: Path,
) -> None:
    root, base, head = synthetic_formal_postcommit(tmp_path)
    state = checker.verify_lifecycle(root, base=base)
    assert state.lifecycle == "post_commit"
    assert state.head == head
    assert len(state.worktrees) == 1
    assert state.worktrees[0][2] == "branch refs/heads/main"
    assert checker.RefRecord("refs/heads/main", head, "commit") in state.refs
    tree = checker._git_result(
        root,
        "ls-tree",
        "-r",
        "-z",
        head,
        "--",
        *(path.as_posix() for path in checker.EXACT10),
    ).stdout
    entries = tuple(item for item in tree.split(b"\0") if item)
    assert len(entries) == 10
    assert all(item.startswith(b"100644 blob ") for item in entries)


@pytest.mark.parametrize("target_kind", ("base", "head"))
def test_formal_postcommit_origin_main_base_or_head_allowed(
    tmp_path: Path,
    target_kind: str,
) -> None:
    root, base, head = synthetic_formal_postcommit(tmp_path)
    target = base if target_kind == "base" else head
    git(root, "update-ref", "refs/remotes/origin/main", target)
    git(
        root,
        "symbolic-ref",
        "refs/remotes/origin/HEAD",
        "refs/remotes/origin/main",
    )
    state = checker.verify_lifecycle(root, base=base)
    assert checker.RefRecord(
        "refs/remotes/origin/main", target, "commit"
    ) in state.refs
    assert checker.RefRecord(
        "refs/remotes/origin/HEAD", target, "commit"
    ) in state.refs


def test_formal_postcommit_origin_main_other_target_rejected(
    tmp_path: Path,
) -> None:
    root, base, head = synthetic_formal_postcommit(tmp_path)
    other = synthetic_other_commit(root, head)
    git(root, "update-ref", "refs/remotes/origin/main", other)
    with pytest.raises(ValueError, match="formal-main post-commit topology"):
        checker.verify_lifecycle(root, base=base)


def test_detached_candidate_two_worktree_postcommit_is_valid(
    tmp_path: Path,
) -> None:
    main, candidate, base, head = synthetic_detached_postcommit(tmp_path)
    state = checker.verify_lifecycle(candidate, base=base)
    assert state.lifecycle == "post_commit"
    assert state.head == head
    assert len(state.worktrees) == 2
    assert any(
        record[0] == os.path.abspath(main)
        and record[1:] == (base, "branch refs/heads/main")
        for record in state.worktrees
    )
    assert any(
        record[0] == os.path.abspath(candidate)
        and record[1:] == (head, "detached")
        for record in state.worktrees
    )
    assert checker.RefRecord("refs/heads/main", base, "commit") in state.refs
    assert all(record.objectname != head for record in state.refs)


def test_detached_postcommit_origin_main_base_allowed(
    tmp_path: Path,
) -> None:
    main, candidate, base, head = synthetic_detached_postcommit(tmp_path)
    git(main, "update-ref", "refs/remotes/origin/main", base)
    git(
        main,
        "symbolic-ref",
        "refs/remotes/origin/HEAD",
        "refs/remotes/origin/main",
    )
    state = checker.verify_lifecycle(candidate, base=base)
    assert checker.RefRecord(
        "refs/remotes/origin/main", base, "commit"
    ) in state.refs
    assert checker.RefRecord(
        "refs/remotes/origin/HEAD", base, "commit"
    ) in state.refs
    assert all(record.objectname != head for record in state.refs)


def test_detached_postcommit_remote_candidate_target_rejected(
    tmp_path: Path,
) -> None:
    main, candidate, base, head = synthetic_detached_postcommit(tmp_path)
    git(main, "update-ref", "refs/remotes/origin/main", head)
    git(
        main,
        "symbolic-ref",
        "refs/remotes/origin/HEAD",
        "refs/remotes/origin/main",
    )
    with pytest.raises(ValueError, match="detached candidate main/base topology"):
        checker.verify_lifecycle(candidate, base=base)


def test_third_worktree_rejected(tmp_path: Path) -> None:
    main, candidate, base, _ = synthetic_detached_postcommit(tmp_path)
    third = tmp_path / "third"
    git(main, "worktree", "add", "--detach", str(third), base)
    with pytest.raises(ValueError, match="topology"):
        checker.verify_lifecycle(candidate, base=base)


def test_postcommit_out_of_scope_history_rejected(
    tmp_path: Path,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    extra = root / "out-of-scope.txt"
    extra.write_bytes(b"out of scope\n")
    git(
        root,
        "add",
        "--",
        *(path.as_posix() for path in checker.EXACT10),
        "out-of-scope.txt",
    )
    git(root, "commit", "-m", "invalid out-of-scope candidate")
    with pytest.raises(ValueError, match="Exact10|out-of-scope"):
        checker.verify_lifecycle(root, base=base)


def test_allow_empty_candidate_history_rejected(tmp_path: Path) -> None:
    root, base, _ = synthetic_formal_postcommit(tmp_path)
    git(root, "commit", "--allow-empty", "-m", "invalid empty successor")
    with pytest.raises(ValueError, match="allow-empty"):
        checker.verify_lifecycle(root, base=base)


@pytest.mark.parametrize("ref_kind", ("branch", "tag"))
def test_extra_branch_or_tag_rejected(
    tmp_path: Path,
    ref_kind: str,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    git(root, ref_kind, "synthetic-residue")
    with pytest.raises(ValueError, match="persistent ref namespace"):
        checker.verify_lifecycle(root, base=base)


@pytest.mark.parametrize("mutation", ("head", "index", "unstaged"))
def test_lifecycle_snapshot_drift_rejected(
    tmp_path: Path,
    mutation: str,
) -> None:
    root, base = synthetic_precommit(tmp_path)
    changed = False

    def mutate(event: str, path: Path) -> None:
        nonlocal changed
        if event != "after_repository_root_open" or changed:
            return
        changed = True
        raw = root / "data/raw/historical-00.txt"
        if mutation == "head":
            git(root, "commit", "--allow-empty", "-m", "HEAD drift")
        elif mutation == "index":
            git(root, "update-index", "--chmod=+x", "--", raw.relative_to(root).as_posix())
        else:
            raw.write_bytes(b"unstaged drift\n")

    with pytest.raises(ValueError, match="drift|dirty"):
        checker.verify_lifecycle(root, base=base, hook=mutate)


def test_after_candidate_validation_ignored_residue_rejected() -> None:
    ordered = tuple(path.as_posix() for path in checker.EXACT10)
    initial = checker._capture_lifecycle_state(
        ROOT,
        ordered,
        base=checker.BASE_COMMIT,
    )
    git_path = Path(
        git(ROOT, "rev-parse", "--git-path", "info/exclude")
        .decode()
        .strip()
    )
    exclude = git_path if git_path.is_absolute() else ROOT / git_path
    original_exclude = exclude.read_bytes()
    extra = checker.DERIVED_ROOT / "ignored-after-candidate-validation.txt"
    absolute_extra = ROOT / extra

    def add_residue() -> None:
        with exclude.open("ab") as stream:
            stream.write(f"/{extra.as_posix()}\n".encode())
        absolute_extra.write_bytes(b"post-validation residue\n")

    try:
        with pytest.raises(ValueError, match="ignored|Exact10"):
            checker._verify_complete_checker_run(
                after_candidate_validation=add_residue
            )
        assert checker._capture_lifecycle_state(
            ROOT,
            ordered,
            base=checker.BASE_COMMIT,
        ) == initial
    finally:
        if absolute_extra.exists():
            absolute_extra.unlink()
        exclude.write_bytes(original_exclude)


def test_final_complete_lifecycle_is_last_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    original_git_result = checker._git_result
    original_read_disk = checker._read_disk
    original_verify = checker.verify_lifecycle

    def observed_git_result(*args: object, **kwargs: object) -> object:
        events.append("git")
        return original_git_result(*args, **kwargs)

    def observed_read_disk(*args: object, **kwargs: object) -> object:
        events.append("disk")
        return original_read_disk(*args, **kwargs)

    def observed_verify(*args: object, **kwargs: object) -> object:
        events.append("verify-start")
        result = original_verify(*args, **kwargs)
        events.append("verify-end")
        return result

    monkeypatch.setattr(checker, "_git_result", observed_git_result)
    monkeypatch.setattr(checker, "_read_disk", observed_read_disk)
    monkeypatch.setattr(checker, "verify_lifecycle", observed_verify)
    report = checker._verify_complete_checker_run()
    assert report["full_recursive_lifecycle_run_count"] == 2
    assert report["final_recursive_lifecycle_is_last_filesystem_validation"]
    assert report["platform_ref_trust_boundary_closure"] is True
    assert report["persistent_ref_namespace_closure"] is True
    assert report["remote_ref_target_closure"] is True
    assert events[-1] == "verify-end"


def test_production_sha_and_frozen_public_runtime_ast() -> None:
    source = (ROOT / checker.PRODUCTION_PATH).read_bytes()
    assert hashlib.sha256(source).hexdigest() == (
        "8810d4bab34b2c5067b51dedb3edaa4a20e25c82c89576265986285e64f59904"
    )
    wanted = {
        "RESULT_SCHEMA_VERSION",
        "RESULT_FIELDS",
        "AGGREGATION_OUTCOME_VOCABULARY",
        "AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES",
        "REASON_VOCABULARY",
        "SCOPE_CONTRACT",
        "CombinedAdmissionCandidateVerdict",
        "_runtime_structure_valid",
        "_aggregation_identity_and_outcome_admissible",
        "_outcome_projections",
        "_verdict",
        "aggregate_admission_rule_evaluations",
    }
    frozen: dict[str, str] = {}
    for node in ast.parse(source).body:
        names: tuple[str, ...] = ()
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            names = (node.name,)
        elif isinstance(node, ast.Assign):
            names = tuple(
                target.id
                for target in node.targets
                if isinstance(target, ast.Name)
            )
        for name in names:
            if name in wanted:
                frozen[name] = ast.dump(node, include_attributes=False)
    assert set(frozen) == wanted
    payload = (
        json.dumps(frozen, separators=(",", ":"), sort_keys=True) + "\n"
    ).encode()
    assert hashlib.sha256(payload).hexdigest() == (
        "65ca999f0042cd795e4f68aed6ce6c873ebaed5818266ee9a56653ddb566a6a8"
    )


def test_no_protected_or_forbidden_candidate_paths() -> None:
    protected = (
        "data/raw/",
        "checkpoints/",
        "equivariant_diffusion/",
        "lightning_modules.py",
        "dataset.py",
        "data/prepare_crossdocked.py",
    )
    for path in production.EXACT10:
        value = path.as_posix()
        assert not any(value == item or value.startswith(item) for item in protected)
        assert path.suffix.lower() not in production.FORBIDDEN_SUFFIXES if hasattr(
            production, "FORBIDDEN_SUFFIXES"
        ) else True
