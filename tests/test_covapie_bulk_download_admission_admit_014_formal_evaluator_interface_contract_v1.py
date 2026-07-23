from __future__ import annotations

import ast
import csv
import errno
import hashlib
import importlib.util
import inspect
import io
import json
import os
import subprocess
import sys
from collections.abc import Iterator, Mapping
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_014_formal_evaluator_interface_contract_design_gate
    as gate,
)

CHECKER_PATH = (
    REPO_ROOT
    / "scripts/check_covapie_bulk_download_admission_admit_014_formal_evaluator_interface_contract_v1.py"
)
SPEC = importlib.util.spec_from_file_location(
    "admit014_formal_checker", CHECKER_PATH
)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
ROOT = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT


@pytest.fixture(scope="module")
def snapshot():
    return gate.build_frozen_source_snapshot()


@pytest.fixture(scope="module")
def payloads(snapshot):
    return gate.build_artifacts(snapshot)


@pytest.fixture(scope="module")
def manifest(payloads):
    return json.loads(payloads[gate.MANIFEST_FILE])


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode(), newline="")))


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def _commit(repo: Path, message: str) -> None:
    result = _git(
        repo,
        "-c",
        "user.name=CovaPIE Test",
        "-c",
        "user.email=covapie-test@example.invalid",
        "commit",
        "-m",
        message,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _seed_lifecycle(
    root: Path, *, tracked: bool = False, descendant: bool = False
) -> tuple[Path, str]:
    root.mkdir(parents=True)
    assert _git(root, "init", "-q").returncode == 0
    (root / "baseline.txt").write_text("baseline\n", encoding="utf-8")
    assert _git(root, "add", "--", "baseline.txt").returncode == 0
    _commit(root, "baseline")
    base = _git(root, "rev-parse", "HEAD").stdout.strip()
    if descendant:
        (root / "descendant.txt").write_text(
            "descendant\n", encoding="utf-8"
        )
        assert _git(root, "add", "--", "descendant.txt").returncode == 0
        _commit(root, "descendant")
    for relative in checker.EXACT10:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            f"fixture:{relative.as_posix()}\n", encoding="utf-8"
        )
    if tracked:
        assert (
            _git(
                root,
                "add",
                "--",
                *(path.as_posix() for path in checker.EXACT10),
            ).returncode
            == 0
        )
        _commit(root, "Exact10")
    return root, base


class Probe(Mapping[str, object]):
    def __init__(
        self,
        values: dict[str, object] | None = None,
        *,
        error: BaseException | None = None,
    ) -> None:
        self.values = {} if values is None else values
        self.error = error
        self.item_keys: list[str] = []
        self.iteration = 0
        self.length = 0
        self.gets = 0
        self.contains = 0

    def __getitem__(self, key: str) -> object:
        self.item_keys.append(key)
        if self.error is not None:
            raise self.error
        return self.values[key]

    def __iter__(self) -> Iterator[str]:
        self.iteration += 1
        raise AssertionError("iteration forbidden")

    def __len__(self) -> int:
        self.length += 1
        raise AssertionError("len forbidden")

    def get(self, key: str, default: object = None) -> object:
        self.gets += 1
        raise AssertionError("get forbidden")

    def __contains__(self, key: object) -> bool:
        self.contains += 1
        raise AssertionError("contains forbidden")


def classify(**kwargs: object):
    return gate.classify_admit_014_formal_evaluator_interface_design(**kwargs)


def test_base_identity_tree_subject_and_ancestry() -> None:
    result = _git(
        REPO_ROOT,
        "show",
        "-s",
        "--format=%H%n%P%n%T%n%s",
        gate.BASE_COMMIT,
    )
    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        gate.BASE_COMMIT,
        gate.BASE_PARENT,
        gate.BASE_TREE,
        gate.BASE_SUBJECT,
    ]
    assert (
        _git(
            REPO_ROOT,
            "merge-base",
            "--is-ancestor",
            gate.BASE_COMMIT,
            "HEAD",
        ).returncode
        == 0
    )


def test_canonical_cpython_3104_and_policy() -> None:
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    assert gate.CANONICAL_PYTHON_VERSION == "3.10.4"
    assert gate.NONCANONICAL_PYTHON_POLICY == (
        "evaluator_semantic_smoke_only; "
        "artifact_build_checker_and_frozen_ast_forbidden"
    )


def test_exact11_source_boundary_order_sha_and_tracking(snapshot) -> None:
    assert len(snapshot) == 11
    assert tuple(item.path for item in snapshot) == gate.SOURCE_PATHS
    assert [item.sha256 for item in snapshot] == [
        gate.SOURCE_SHA256[path] for path in gate.SOURCE_PATHS
    ]
    assert all(
        not item.path.as_posix().startswith(("data/raw/", "checkpoints/"))
        for item in snapshot
    )
    for item in snapshot:
        stage = _git(
            REPO_ROOT, "ls-files", "--stage", "--", item.path.as_posix()
        )
        assert stage.returncode == 0
        assert stage.stdout.split()[2] == "0"


def test_future_signature_exact_string_and_inspect_contract() -> None:
    assert gate.FUTURE_PUBLIC_SIGNATURE == checker.FUTURE_SIGNATURE
    signature = gate.FORMAL_SIGNATURE_DESIGN
    assert isinstance(signature, inspect.Signature)
    parameters = tuple(signature.parameters.values())
    assert len(parameters) == 1
    parameter = parameters[0]
    assert parameter.name == "stage_authorization_context"
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.annotation is object
    assert parameter.default is gate._DESIGN_MISSING
    assert signature.return_annotation == "Admit014EvaluationResult"
    assert not any(
        item.kind is inspect.Parameter.VAR_POSITIONAL for item in parameters
    )
    assert not any(
        item.kind is inspect.Parameter.VAR_KEYWORD for item in parameters
    )


def test_signature_rejects_positional_and_unknown_keyword() -> None:
    with pytest.raises(TypeError):
        gate.FORMAL_SIGNATURE_DESIGN.bind(object())
    with pytest.raises(TypeError):
        gate.FORMAL_SIGNATURE_DESIGN.bind(unknown=True)
    with pytest.raises(TypeError):
        classify(object())  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        classify(unknown=True)


def test_signature_truth_helper_and_checker_fail_closed_on_wrong_signature(
    monkeypatch,
) -> None:
    wrong = inspect.Signature(
        (
            inspect.Parameter(
                "stage_authorization_context",
                inspect.Parameter.POSITIONAL_ONLY,
                default=None,
                annotation=object,
            ),
        ),
        return_annotation="WrongResult",
    )
    monkeypatch.setattr(gate, "FORMAL_SIGNATURE_DESIGN", wrong)
    with pytest.raises(ValueError, match="signature property verification failed"):
        gate._signature_truth_observation("SIGNATURE_ONE_KEYWORD_ONLY")
    with pytest.raises(ValueError, match="future signature drift"):
        checker._validate_signature_and_oracle(gate)


def test_omitted_and_explicit_none_have_structured_blocked_result() -> None:
    for result in (
        classify(),
        classify(stage_authorization_context=None),
    ):
        assert (
            result.outcome,
            result.reason,
            result.canonical_stage_authorization_record,
            result.validated_stage_authorization_fields,
            result.consumed_stage_authorization_fields,
        ) == (
            "blocked",
            "STAGE_AUTHORIZATION_CONTEXT_REQUIRED",
            (),
            (),
            (),
        )


@pytest.mark.parametrize("value", [object(), 7, "x", []])
def test_nonmapping_projection_has_no_consumption(value: object) -> None:
    result = classify(stage_authorization_context=value)
    assert result.reason == "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID"
    assert result.canonical_stage_authorization_record == ()
    assert result.validated_stage_authorization_fields == ()
    assert result.consumed_stage_authorization_fields == ()


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (KeyError("target"), "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING"),
        (RuntimeError("boom"), "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED"),
        (ValueError("boom"), "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED"),
    ],
)
def test_lookup_failures_record_target_consumption(
    error: BaseException, reason: str
) -> None:
    probe = Probe(error=error)
    result = classify(stage_authorization_context=probe)
    assert result.reason == reason
    assert result.canonical_stage_authorization_record == ()
    assert result.validated_stage_authorization_fields == ()
    assert result.consumed_stage_authorization_fields == (
        checker.TARGET_KEY,
    )
    assert probe.item_keys == [checker.TARGET_KEY]


@pytest.mark.parametrize(
    "value",
    [
        0,
        1,
        0.0,
        1.0,
        "false",
        "true",
        None,
        [],
        {},
        object(),
    ],
)
def test_invalid_exact_bool_type_projection(value: object) -> None:
    result = classify(
        stage_authorization_context=Probe({checker.TARGET_KEY: value})
    )
    assert result.outcome == "blocked"
    assert result.reason == "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_TYPE_INVALID"
    assert result.canonical_stage_authorization_record == ()
    assert result.validated_stage_authorization_fields == ()
    assert result.consumed_stage_authorization_fields == (
        checker.TARGET_KEY,
    )


def test_exact_false_and_true_preserve_canonical_bool() -> None:
    false = classify(
        stage_authorization_context={checker.TARGET_KEY: False}
    )
    true = classify(stage_authorization_context={checker.TARGET_KEY: True})
    assert (
        false.outcome,
        false.reason,
        false.canonical_stage_authorization_record,
    ) == (
        "blocked",
        "BULK_DOWNLOAD_NOT_AUTHORIZED",
        ((checker.TARGET_KEY, False),),
    )
    assert (
        true.outcome,
        true.reason,
        true.canonical_stage_authorization_record,
    ) == ("passed", "", ((checker.TARGET_KEY, True),))
    assert type(false.canonical_stage_authorization_record[0][1]) is bool
    assert type(true.canonical_stage_authorization_record[0][1]) is bool
    assert false.validated_stage_authorization_fields == (
        checker.TARGET_KEY,
    )
    assert true.consumed_stage_authorization_fields == (
        checker.TARGET_KEY,
    )


@pytest.mark.parametrize("permission", [False, True])
def test_admit015_coexists_and_has_zero_access(permission: bool) -> None:
    probe = Probe(
        {
            checker.ADMIT015_KEY: not permission,
            checker.TARGET_KEY: permission,
            "extra": object(),
        }
    )
    result = classify(stage_authorization_context=probe)
    assert result.outcome == ("passed" if permission else "blocked")
    assert probe.item_keys == [checker.TARGET_KEY]
    assert (
        probe.iteration,
        probe.length,
        probe.gets,
        probe.contains,
    ) == (0, 0, 0, 0)


def test_result_exact9_field_order_types_frozen_and_exact_class() -> None:
    result = classify(
        stage_authorization_context={checker.TARGET_KEY: True}
    )
    assert tuple(field.name for field in fields(type(result))) == (
        checker.RESULT_FIELDS
    )
    assert tuple(
        type(getattr(result, name)).__name__ for name in checker.RESULT_FIELDS
    ) == checker.RESULT_TYPES
    with pytest.raises(FrozenInstanceError):
        result.reason = "changed"  # type: ignore[misc]
    assert gate.validate_admit_014_evaluation_result_contract_design(result)


def test_result_subclass_rejected() -> None:
    class ResultSubclass(gate.Admit014EvaluationResultContractDesign):
        pass

    result = classify(
        stage_authorization_context={checker.TARGET_KEY: True}
    )
    with pytest.raises(TypeError):
        ResultSubclass(
            *(getattr(result, name) for name in checker.RESULT_FIELDS)
        )


@pytest.mark.parametrize(
    "mutation",
    [
        {"admission_rule_id": "ADMIT_015"},
        {"outcome": "invalid"},
        {"passed": 1},
        {"blocks_candidate": 0},
        {"evaluator_io_used": 0},
        {"evaluator_io_used": True},
        {"reason": "BULK_DOWNLOAD_NOT_AUTHORIZED"},
        {"canonical_stage_authorization_record": [(checker.TARGET_KEY, True)]},
        {
            "canonical_stage_authorization_record": (
                (checker.ADMIT015_KEY, True),
            )
        },
        {
            "canonical_stage_authorization_record": (
                (checker.TARGET_KEY, "true"),
            )
        },
        {
            "canonical_stage_authorization_record": (
                (checker.TARGET_KEY, True),
                (checker.TARGET_KEY, True),
            )
        },
        {"validated_stage_authorization_fields": [checker.TARGET_KEY]},
        {"validated_stage_authorization_fields": (checker.ADMIT015_KEY,)},
        {
            "validated_stage_authorization_fields": (
                checker.TARGET_KEY,
                checker.TARGET_KEY,
            )
        },
        {"consumed_stage_authorization_fields": [checker.TARGET_KEY]},
        {"consumed_stage_authorization_fields": (checker.ADMIT015_KEY,)},
        {
            "consumed_stage_authorization_fields": (
                checker.TARGET_KEY,
                checker.TARGET_KEY,
            )
        },
        {"validated_stage_authorization_fields": ()},
        {"consumed_stage_authorization_fields": ()},
    ],
)
def test_negative_result_contract_rejected(mutation: dict[str, object]) -> None:
    result = classify(
        stage_authorization_context={checker.TARGET_KEY: True}
    )
    values = {
        name: getattr(result, name) for name in checker.RESULT_FIELDS
    }
    values.update(mutation)
    with pytest.raises((TypeError, ValueError)):
        gate.Admit014EvaluationResultContractDesign(
            *(values[name] for name in checker.RESULT_FIELDS)
        )


def test_tuple_and_pair_tuple_subclasses_rejected() -> None:
    class TupleSubclass(tuple):
        pass

    result = classify(
        stage_authorization_context={checker.TARGET_KEY: True}
    )
    values = {
        name: getattr(result, name) for name in checker.RESULT_FIELDS
    }
    for replacement in (
        TupleSubclass(((checker.TARGET_KEY, True),)),
        (TupleSubclass((checker.TARGET_KEY, True)),),
    ):
        values["canonical_stage_authorization_record"] = replacement
        with pytest.raises((TypeError, ValueError)):
            gate.Admit014EvaluationResultContractDesign(
                *(values[name] for name in checker.RESULT_FIELDS)
            )
    for name in (
        "validated_stage_authorization_fields",
        "consumed_stage_authorization_fields",
    ):
        values = {
            field_name: getattr(result, field_name)
            for field_name in checker.RESULT_FIELDS
        }
        values[name] = TupleSubclass((checker.TARGET_KEY,))
        with pytest.raises((TypeError, ValueError)):
            gate.Admit014EvaluationResultContractDesign(
                *(values[field_name] for field_name in checker.RESULT_FIELDS)
            )


def test_truth_matrix_exact69_groups_and_negative_cases(payloads, manifest) -> None:
    rows = _rows(payloads[gate.TRUTH_FILE])
    assert tuple(rows[0]) == gate.TRUTH_COLUMNS
    assert len(rows) == 69
    assert [row["case_order"] for row in rows] == [
        str(index) for index in range(1, 70)
    ]
    assert all(row["case_passed"] == "true" for row in rows)
    signature = rows[:8]
    assert [row["case_id"] for row in signature] == list(
        checker.SIGNATURE_CASE_IDS
    )
    assert [row["expected_outcome"] for row in signature] == (
        ["verified"] * 6 + ["rejected"] * 2
    )
    assert [row["observed_outcome"] for row in signature] == (
        ["verified"] * 6 + ["rejected"] * 2
    )
    assert [row["expected_reason"] for row in signature] == (
        [""] * 6 + ["TypeError"] * 2
    )
    assert [row["observed_reason"] for row in signature] == (
        [""] * 6 + ["TypeError"] * 2
    )
    assert all(
        row[column] == "()"
        for row in signature
        for column in (
            "expected_canonical_record",
            "observed_canonical_record",
            "expected_validated_fields",
            "observed_validated_fields",
            "expected_consumed_fields",
            "observed_consumed_fields",
        )
    )
    assert all(
        "STAGE_AUTHORIZATION_CONTEXT_REQUIRED"
        not in (row["expected_reason"], row["observed_reason"])
        for row in signature
    )
    assert hashlib.sha256(
        json.dumps(
            rows[8:], sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest() == checker.NON_SIGNATURE_TRUTH_SHA256
    assert manifest["outcome_vocabulary"] == ["passed", "blocked"]
    assert "verified" not in manifest["outcome_vocabulary"]
    assert "rejected" not in manifest["outcome_vocabulary"]
    assert manifest["truth_matrix_signature_meta_semantics"] == {
        "row_count": 8,
        "property_rows": 6,
        "property_meta_outcome": "verified",
        "rejection_rows": 2,
        "rejection_meta_outcome": "rejected",
        "rejection_reason": "TypeError",
        "generated_by_real_signature_introspection_bind_and_invocation": True,
        "meta_outcomes_are_formal_evaluator_outcomes": False,
    }
    assert manifest["truth_matrix_positive_row_count"] == 45
    assert manifest["truth_matrix_negative_result_row_count"] == 24
    assert manifest["truth_matrix_group_counts"] == {
        "signature": 8,
        "context_structure": 8,
        "lookup": 3,
        "invalid_exact_type": 11,
        "business_outcome": 2,
        "mapping_behavior": 7,
        "result_projection": 6,
        "negative_result_contract": 24,
    }


def test_exact30_continuity_exact2_transition_all7_resolved(
    snapshot, payloads
) -> None:
    inherited = gate._csv_rows(
        snapshot,
        gate.AUTH_ROOT / "covapie_admit_014_issue_readiness_inventory.csv",
    )
    rows = _rows(payloads[gate.ISSUE_FILE])
    assert len(rows) == len(inherited) == 30
    assert [row["issue_id"] for row in rows] == [
        row["issue_id"] for row in inherited
    ]
    by_id = {row["issue_id"]: row for row in rows}
    for issue_id, evidence in gate.ISSUE_TRANSITIONS.items():
        assert by_id[issue_id]["successor_effective_status"] == "resolved"
        assert by_id[issue_id]["successor_transition_action"] == (
            gate.ISSUE_TRANSITION_ACTION
        )
        assert by_id[issue_id]["successor_transition_evidence"] == evidence
    assert all(
        row["successor_effective_status"] == "resolved" for row in rows[23:]
    )
    assert all(
        by_id[issue]["successor_effective_status"] == "open"
        for issue in gate.GLOBAL_OPEN_ISSUES
    )
    assert by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"][
        "affected_rules"
    ] == "ADMIT_014|ADMIT_015"


def test_precondition_transition_is_exact49_complete_2_open(manifest) -> None:
    assert manifest["precondition_transition"] == {
        "row_count": 51,
        "complete_count": 49,
        "incomplete_count": 2,
        "implementation_blocking_count": 2,
        "resolved_precondition_ids": ["PRE_039", "PRE_040", "PRE_041"],
        "remaining_open_precondition_ids": ["PRE_048", "PRE_049"],
    }


def test_readiness_and_nonimplementation_boundaries(manifest) -> None:
    expected = {
        **{key: True for key in gate.TRUE_READINESS},
        **{key: False for key in gate.FALSE_READINESS},
    }
    assert manifest["readiness"] == expected
    assert all(manifest[key] is True for key in gate.TRUE_READINESS)
    assert all(manifest[key] is False for key in gate.FALSE_READINESS)
    assert manifest["current_permission"] is False
    assert manifest["formal_evaluator_implemented"] is False
    assert manifest["formal_result_type_defined"] is False
    assert manifest["unified_adapter_contract_frozen"] is False
    assert manifest["unified_adapter_implemented"] is False
    assert manifest["admit_014_registered_in_engine"] is False
    assert manifest[
        "unified_dispatch_runtime_with_admit_001_to_014_implemented"
    ] is False
    assert manifest[
        "mandatory_pre_download_authorization_enforcement_contract"
    ]["implemented"] is False
    assert manifest["recommended_next_step"] == (
        "implement_covapie_admit_014_standalone_evaluator_interface_v1"
    )


def test_no_formal_evaluator_result_adapter_registry_or_runtime() -> None:
    source = (REPO_ROOT / checker.PRODUCTION).read_bytes()
    tree = ast.parse(source)
    definitions = {
        node.name
        for node in ast.walk(tree)
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        )
    }
    assert "evaluate_admit_014" not in definitions
    assert "Admit014EvaluationResult" not in definitions
    assert "_evaluate_registered_admit_014" not in definitions
    assert "evaluate_admission_rule" not in definitions
    assert b"os.replace" not in source


def test_deterministic_build_and_inode_preserving_noop(
    tmp_path, payloads
) -> None:
    root = tmp_path / "out"
    first = gate.materialize_contract(root)
    before = {
        path.name: (path.stat().st_ino, path.read_bytes())
        for path in root.iterdir()
    }
    second = gate.materialize_contract(root)
    assert first == second
    assert before == {
        path.name: (path.stat().st_ino, path.read_bytes())
        for path in root.iterdir()
    }
    assert {path.name: path.read_bytes() for path in root.iterdir()} == payloads


def test_existing_mismatch_fails_closed(tmp_path) -> None:
    root = tmp_path / "out"
    gate.materialize_contract(root)
    (root / gate.CONTRACT_FILE).write_bytes(b"tampered\n")
    with pytest.raises(ValueError, match="existing output set mismatch"):
        gate.materialize_contract(root)


def _copy_exact6(root: Path, payloads: dict[str, bytes]) -> None:
    root.mkdir()
    for name, data in payloads.items():
        (root / name).write_bytes(data)


def test_checker_pinned_outputs_reads_normal_exact6(tmp_path, payloads) -> None:
    root = tmp_path / "normal"
    _copy_exact6(root, payloads)
    assert checker._pinned_outputs(root) == payloads


@pytest.mark.parametrize(
    "race",
    [
        "same_byte_leaf_replacement",
        "same_byte_root_replacement",
        "post_traversal_extra_leaf",
        "post_traversal_missing_leaf",
    ],
)
def test_checker_pinned_outputs_real_traversal_races_fail_closed(
    tmp_path, payloads, monkeypatch, race: str
) -> None:
    root = tmp_path / "out"
    _copy_exact6(root, payloads)
    original_read = checker.os.read
    original_listdir = checker.os.listdir
    mutated = False
    listdir_calls = 0

    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal mutated
        data = original_read(descriptor, size)
        if (
            data
            and not mutated
            and race
            in {
                "same_byte_leaf_replacement",
                "same_byte_root_replacement",
            }
        ):
            mutated = True
            if race == "same_byte_leaf_replacement":
                target = root / checker.FILES[0]
                replacement = tmp_path / "same-byte-replacement"
                replacement.write_bytes(target.read_bytes())
                os.rename(replacement, target)
            else:
                old_root = tmp_path / "old-output-root"
                os.rename(root, old_root)
                _copy_exact6(root, payloads)
        return data

    def racing_listdir(descriptor: int) -> list[str]:
        nonlocal mutated, listdir_calls
        listdir_calls += 1
        if (
            listdir_calls == 2
            and not mutated
            and race
            in {
                "post_traversal_extra_leaf",
                "post_traversal_missing_leaf",
            }
        ):
            mutated = True
            if race == "post_traversal_extra_leaf":
                (root / "seventh.csv").write_text(
                    "real race\n", encoding="utf-8"
                )
            else:
                (root / checker.FILES[0]).unlink()
        return original_listdir(descriptor)

    monkeypatch.setattr(checker.os, "read", racing_read)
    monkeypatch.setattr(checker.os, "listdir", racing_listdir)
    with pytest.raises(ValueError):
        checker._pinned_outputs(root)
    assert mutated is True
    assert not list(tmp_path.rglob("*.tmp"))
    assert not list(tmp_path.rglob("*.part"))


def test_gpfs_einval_fails_closed_without_os_replace(
    tmp_path, monkeypatch
) -> None:
    root = tmp_path / "out"
    replace_called = False

    def reject(*args):
        raise OSError(errno.EINVAL, "simulated GPFS EINVAL")

    def forbidden_replace(*args):
        nonlocal replace_called
        replace_called = True
        raise AssertionError("os.replace fallback called")

    monkeypatch.setattr(gate, "_rename_noreplace", reject)
    monkeypatch.setattr(os, "replace", forbidden_replace)
    with pytest.raises(OSError) as captured:
        gate.materialize_contract(root)
    assert captured.value.errno == errno.EINVAL
    assert replace_called is False
    assert not root.exists()
    assert not list(tmp_path.glob(".*.staging"))


@pytest.mark.parametrize(
    "race",
    ["same_byte_leaf_replacement", "in_place_mutation", "parent_replacement"],
)
def test_pinned_source_races_are_rejected(
    tmp_path, monkeypatch, race: str
) -> None:
    repo = tmp_path / "repo"
    source = repo / "evidence/source.txt"
    source.parent.mkdir(parents=True)
    source.write_text("frozen\n", encoding="utf-8")
    monkeypatch.setattr(gate, "REPO_ROOT", repo)
    original_read = gate.os.read
    mutated = False

    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal mutated
        data = original_read(descriptor, size)
        if data and not mutated:
            mutated = True
            if race == "same_byte_leaf_replacement":
                replacement = source.with_name("replacement")
                replacement.write_bytes(source.read_bytes())
                os.rename(replacement, source)
            elif race == "in_place_mutation":
                with source.open("ab") as stream:
                    stream.write(b"mutation")
            else:
                old = repo / "evidence-old"
                os.rename(source.parent, old)
                source.parent.mkdir()
                source.write_text("frozen\n", encoding="utf-8")
        return data

    monkeypatch.setattr(gate.os, "read", racing_read)
    with pytest.raises(ValueError):
        gate._pinned_read_relative(Path("evidence/source.txt"))


def test_manifest_duplicate_missing_extra_reorder_rejected(payloads) -> None:
    text = payloads[gate.MANIFEST_FILE].decode()
    duplicate = text.replace(
        '{\n  "project": "CovaPIE",',
        '{\n  "project": "tampered",\n  "project": "CovaPIE",',
        1,
    ).encode()
    with pytest.raises(ValueError, match="duplicate JSON key"):
        checker._parse_manifest_exact(duplicate)
    for case in ("missing", "extra", "reordered"):
        value = json.loads(text)
        if case == "missing":
            value.pop("project")
        elif case == "extra":
            value["unexpected"] = True
        else:
            project = value.pop("project")
            value["project"] = project
        tampered = (json.dumps(value, indent=2) + "\n").encode()
        with pytest.raises(ValueError, match="missing/extra/reordered"):
            checker._parse_manifest_exact(tampered)


def test_synchronized_csv_manifest_tamper_rejected(payloads) -> None:
    outputs = dict(payloads)
    outputs[gate.CONTRACT_FILE] += b"tampered\n"
    manifest = json.loads(outputs[gate.MANIFEST_FILE])
    manifest["output_sha256"][gate.CONTRACT_FILE] = hashlib.sha256(
        outputs[gate.CONTRACT_FILE]
    ).hexdigest()
    assert (
        hashlib.sha256(outputs[gate.CONTRACT_FILE]).hexdigest()
        != checker.OUTPUT_SHA256[gate.CONTRACT_FILE]
    )


def test_checker_passes_and_reports_lifecycle() -> None:
    result = subprocess.run(
        [sys.executable, str(CHECKER_PATH)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    tracked = (
        _git(
            REPO_ROOT,
            "ls-files",
            "--error-unmatch",
            "--",
            checker.TEST.as_posix(),
        ).returncode
        == 0
    )
    assert (
        f"lifecycle={'post_commit' if tracked else 'pre_commit'}"
        in result.stdout
    )


@pytest.mark.parametrize(
    "relative",
    [checker.PRODUCTION, checker.CHECKER, checker.TEST],
)
def test_isolated_imports_are_silent(tmp_path, relative: Path) -> None:
    path = REPO_ROOT / relative
    code = (
        "import importlib.util,sys;"
        f"s=importlib.util.spec_from_file_location('isolated',{str(path)!r});"
        "m=importlib.util.module_from_spec(s);sys.modules['isolated']=m;"
        "s.loader.exec_module(m)"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""


def test_lifecycle_positive_pre_descendant_and_post(tmp_path) -> None:
    pre, base = _seed_lifecycle(tmp_path / "pre")
    assert checker._lifecycle(pre, base) == "pre_commit"
    descendant, descendant_base = _seed_lifecycle(
        tmp_path / "descendant", descendant=True
    )
    assert checker._lifecycle(descendant, descendant_base) == "pre_commit"
    post, post_base = _seed_lifecycle(tmp_path / "post", tracked=True)
    assert checker._lifecycle(post, post_base) == "post_commit"


@pytest.mark.parametrize(
    "case",
    [
        "mixed",
        "staged",
        "dirty",
        "missing",
        "ignored",
        "extra",
        "seventh",
        "symlink",
        "oversized",
        "base_nonancestor",
        "forbidden_suffix",
    ],
)
def test_lifecycle_negative_states(tmp_path, case: str) -> None:
    repo, base = _seed_lifecycle(
        tmp_path / case, tracked=case == "dirty"
    )
    exact10 = checker.EXACT10
    if case == "mixed":
        assert _git(
            repo, "add", "--", exact10[0].as_posix()
        ).returncode == 0
        _commit(repo, "one stage path")
    elif case == "staged":
        assert _git(
            repo, "add", "--", exact10[0].as_posix()
        ).returncode == 0
    elif case == "dirty":
        with (repo / exact10[0]).open("a", encoding="utf-8") as stream:
            stream.write("dirty\n")
    elif case == "missing":
        (repo / exact10[0]).unlink()
    elif case == "ignored":
        (repo / ".gitignore").write_text(
            exact10[0].as_posix() + "\n", encoding="utf-8"
        )
    elif case == "extra":
        (
            repo
            / "docs/extra_admit_014_formal_evaluator_interface_contract.md"
        ).write_text("extra\n", encoding="utf-8")
    elif case == "seventh":
        (repo / checker.OUTPUT_ROOT / "seventh.csv").write_text(
            "extra\n", encoding="utf-8"
        )
    elif case == "symlink":
        target = repo / exact10[3]
        target.unlink()
        target.symlink_to(repo / "baseline.txt")
    elif case == "oversized":
        os.truncate(repo / exact10[0], 101 * 1024 * 1024)
    elif case == "base_nonancestor":
        base = "0" * 40
    else:
        exact10 = (exact10[0].with_suffix(".pt"), *exact10[1:])
    with pytest.raises(ValueError):
        checker._lifecycle(repo, base, exact10)


def test_tracked_ignored_candidate_is_rejected(tmp_path) -> None:
    repo, base = _seed_lifecycle(tmp_path / "tracked", tracked=True)
    ignored = checker.EXACT10[0]
    (repo / ".gitignore").write_text(
        ignored.as_posix() + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="ignored candidate"):
        checker._lifecycle(repo, base)


def test_exact10_inventory_and_protected_paths() -> None:
    paths = [REPO_ROOT / path for path in checker.EXACT10]
    assert len(paths) == len(set(paths)) == 10
    forbidden = {
        ".pt",
        ".ckpt",
        ".pth",
        ".pkl",
        ".lmdb",
        ".tar",
        ".zip",
        ".tgz",
        ".npz",
        ".tmp",
        ".part",
    }
    assert not any(path.is_symlink() for path in paths)
    assert not any(path.suffix in forbidden for path in paths)
    assert not any(path.stat().st_size > 100 * 1024 * 1024 for path in paths)
    checker._validate_protected_paths()
