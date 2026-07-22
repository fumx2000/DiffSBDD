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
import shutil
import subprocess
import sys
from dataclasses import fields
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (
    covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_design_gate
    as gate,
)


CHECKER_PATH = ROOT / "scripts/check_covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1.py"
OUTPUT_ROOT = ROOT / gate.DEFAULT_OUTPUT_ROOT
AUTHORIZED_FILES = {
    "src/covalent_ext/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_design_gate.py",
    "scripts/check_covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1.py",
    "tests/test_covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1.py",
    "docs/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1_summary.md",
    *(f"{gate.DEFAULT_OUTPUT_ROOT.as_posix()}/{name}" for name in gate.OUTPUT_FILES),
}


def _load_checker():
    specification = importlib.util.spec_from_file_location("admit012_formal_checker", CHECKER_PATH)
    assert specification and specification.loader
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _valid_kwargs() -> dict[str, object]:
    return {
        "download_result_status": "success",
        "observed_http_status": 200,
        "observed_content_length_bytes": 1,
        "observed_sha256": "0123456789abcdef" * 4,
        **dict(zip(gate.EXACT4_CONTEXT_ITEMS, gate.FORMAL_CONTEXT_VALUES, strict=True)),
    }


def _result(**updates: object) -> gate.Admit012EvaluationResultContractDesign:
    baseline = gate.classify_admit_012_formal_evaluator_interface_design(**_valid_kwargs())
    values = {name: getattr(baseline, name) for name in gate.RESULT_FIELDS}
    values.update(updates)
    return gate.Admit012EvaluationResultContractDesign(*(values[name] for name in gate.RESULT_FIELDS))


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode(), newline="")))


def test_signature_exact_parameter_order() -> None:
    assert tuple(gate.FORMAL_SIGNATURE_DESIGN.parameters) == (*gate.EXACT4_FIELDS, *gate.EXACT4_CONTEXT_ITEMS)


def test_signature_is_entirely_keyword_only() -> None:
    assert {parameter.kind for parameter in gate.FORMAL_SIGNATURE_DESIGN.parameters.values()} == {
        inspect.Parameter.KEYWORD_ONLY
    }


def test_exact4_share_one_private_missing_default() -> None:
    parameters = tuple(gate.FORMAL_SIGNATURE_DESIGN.parameters.values())
    defaults = tuple(parameter.default for parameter in parameters[:4])
    assert all(value is defaults[0] is gate._MISSING for value in defaults)
    assert type(defaults[0]).__name__.startswith("_Missing")


def test_exact4_contexts_are_required() -> None:
    parameters = tuple(gate.FORMAL_SIGNATURE_DESIGN.parameters.values())
    assert all(parameter.default is inspect.Parameter.empty for parameter in parameters[4:])


def test_signature_has_no_varargs_or_varkw() -> None:
    signature = inspect.signature(gate.classify_admit_012_formal_evaluator_interface_design)
    assert all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in signature.parameters.values())
    assert not any(parameter.kind in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}
                   for parameter in signature.parameters.values())


@pytest.mark.parametrize("context_index", range(4))
def test_context_exact_tuple_requirement(context_index: int) -> None:
    kwargs = _valid_kwargs()
    kwargs[gate.EXACT4_CONTEXT_ITEMS[context_index]] = list(gate.FORMAL_CONTEXT_VALUES[context_index])
    result = gate.classify_admit_012_formal_evaluator_interface_design(**kwargs)
    assert result.reason == gate.CONTEXT_REASONS[context_index * 2]


@pytest.mark.parametrize("context_index", range(4))
def test_context_tuple_subclass_rejected(context_index: int) -> None:
    kwargs = _valid_kwargs()
    kwargs[gate.EXACT4_CONTEXT_ITEMS[context_index]] = gate._TupleSubclass(
        gate.FORMAL_CONTEXT_VALUES[context_index]
    )
    result = gate.classify_admit_012_formal_evaluator_interface_design(**kwargs)
    assert result.reason == gate.CONTEXT_REASONS[context_index * 2]


@pytest.mark.parametrize("context_index", (1, 2, 3))
def test_context_pair_exact_shape_order_and_types(context_index: int) -> None:
    expected = gate.FORMAL_CONTEXT_VALUES[context_index]
    mutations = (
        (list(expected[0]), *expected[1:]),
        (expected[1], expected[0], *expected[2:]),
        (("wrong_key", expected[0][1]), *expected[1:]),
    )
    for mutation in mutations:
        kwargs = _valid_kwargs()
        kwargs[gate.EXACT4_CONTEXT_ITEMS[context_index]] = mutation
        assert gate.classify_admit_012_formal_evaluator_interface_design(**kwargs).reason == (
            gate.CONTEXT_REASONS[context_index * 2 + 1]
        )


@pytest.mark.parametrize("context_index", (1, 2, 3))
def test_context_bool_int_distinction(context_index: int) -> None:
    expected = gate.FORMAL_CONTEXT_VALUES[context_index]
    mutation = ((expected[0][0], True), *expected[1:])
    kwargs = _valid_kwargs()
    kwargs[gate.EXACT4_CONTEXT_ITEMS[context_index]] = mutation
    assert gate.classify_admit_012_formal_evaluator_interface_design(**kwargs).reason == (
        gate.CONTEXT_REASONS[context_index * 2 + 1]
    )


def test_exact10_result_order() -> None:
    assert tuple(field.name for field in fields(gate.Admit012EvaluationResultContractDesign)) == gate.RESULT_FIELDS


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (("admission_rule_id", 12), ("passed", 1), ("canonical_download_result_record", []),
     ("consumed_context_items", ["allowed_download_result_statuses"])),
)
def test_result_fields_require_exact_builtin_types(field_name: str, bad_value: object) -> None:
    with pytest.raises(TypeError):
        _result(**{field_name: bad_value})


@pytest.mark.parametrize(
    "updates",
    (
        {"passed": False},
        {"blocks_candidate": True},
        {"reason": "DOWNLOAD_RESULT_STATUS_MISSING"},
    ),
)
def test_passed_outcome_invariants_fail_closed(updates: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        _result(**updates)


@pytest.mark.parametrize("missing_index", range(4))
def test_missing_maps_to_blocked(missing_index: int) -> None:
    kwargs = _valid_kwargs()
    kwargs.pop(gate.EXACT4_FIELDS[missing_index])
    result = gate.classify_admit_012_formal_evaluator_interface_design(**kwargs)
    assert (result.outcome, result.reason, result.consumed_download_result_fields) == (
        "blocked", gate.MISSING_REASONS[missing_index], gate.EXACT4_FIELDS[:missing_index + 1]
    )


@pytest.mark.parametrize(
    ("field_index", "bad_value", "reason"),
    (
        (0, None, gate.TYPE_INVALID_REASONS[0]), (0, "pending", gate.VALUE_INVALID_REASONS[0]),
        (1, True, gate.TYPE_INVALID_REASONS[1]), (1, 600, gate.VALUE_INVALID_REASONS[1]),
        (2, True, gate.TYPE_INVALID_REASONS[2]), (2, -1, gate.VALUE_INVALID_REASONS[2]),
        (3, b"0" * 64, gate.TYPE_INVALID_REASONS[3]), (3, "A" * 64, gate.VALUE_INVALID_REASONS[3]),
    ),
)
def test_field_invalid_maps_to_invalid(field_index: int, bad_value: object, reason: str) -> None:
    kwargs = _valid_kwargs()
    kwargs[gate.EXACT4_FIELDS[field_index]] = bad_value
    result = gate.classify_admit_012_formal_evaluator_interface_design(**kwargs)
    assert (result.outcome, result.reason) == ("invalid", reason)


@pytest.mark.parametrize("context_index", range(4))
def test_context_invalid_maps_to_invalid(context_index: int) -> None:
    kwargs = _valid_kwargs()
    kwargs[gate.EXACT4_CONTEXT_ITEMS[context_index]] = []
    result = gate.classify_admit_012_formal_evaluator_interface_design(**kwargs)
    assert (result.outcome, result.reason) == ("invalid", gate.CONTEXT_REASONS[context_index * 2])


def test_canonical_record_is_empty_before_complete_field_validation() -> None:
    kwargs = _valid_kwargs()
    kwargs["observed_sha256"] = "bad"
    result = gate.classify_admit_012_formal_evaluator_interface_design(**kwargs)
    assert result.canonical_download_result_record == ()


@pytest.mark.parametrize("failure_index", range(4))
def test_validated_fields_are_prefix_excluding_failure(failure_index: int) -> None:
    kwargs = _valid_kwargs()
    kwargs[gate.EXACT4_FIELDS[failure_index]] = None
    result = gate.classify_admit_012_formal_evaluator_interface_design(**kwargs)
    assert tuple(name for name, _ in result.validated_download_result_fields) == gate.EXACT4_FIELDS[:failure_index]


def test_consumed_fields_follow_presence_then_validation_phases() -> None:
    missing = _valid_kwargs()
    missing.pop("observed_http_status")
    invalid = _valid_kwargs()
    invalid["download_result_status"] = None
    assert gate.classify_admit_012_formal_evaluator_interface_design(**missing).consumed_download_result_fields == gate.EXACT4_FIELDS[:2]
    assert gate.classify_admit_012_formal_evaluator_interface_design(**invalid).consumed_download_result_fields == gate.EXACT4_FIELDS


@pytest.mark.parametrize("context_index", range(4))
def test_consumed_context_is_actual_prefix(context_index: int) -> None:
    kwargs = _valid_kwargs()
    kwargs[gate.EXACT4_CONTEXT_ITEMS[context_index]] = []
    result = gate.classify_admit_012_formal_evaluator_interface_design(**kwargs)
    assert result.consumed_context_items == gate.EXACT4_CONTEXT_ITEMS[:context_index + 1]


def test_all52_predecessor_truth_cases_are_projected_unchanged() -> None:
    artifacts = gate.build_artifacts()
    rows = _rows(artifacts[gate.TRUTH_FILE])[:52]
    predecessor = _rows((ROOT / gate.FIELD_STAGE / "covapie_admit_012_download_integrity_validation_truth_matrix.csv").read_bytes())
    assert len(rows) == len(predecessor) == 52
    assert [row["case_id"] for row in rows] == [f"FIELD52_{row['case_id']}" for row in predecessor]
    for current, prior in zip(rows, predecessor, strict=True):
        assert tuple(current[column] for column in gate.TRUTH_COLUMNS[4:8]) == tuple(
            prior[column] for column in gate.TRUTH_COLUMNS[4:8]
        )


def test_context_type_and_content_truth_cases_are_complete() -> None:
    rows = _rows(gate.build_artifacts()[gate.TRUTH_FILE])
    context_rows = [row for row in rows if row["case_group"] == "context_validation"]
    assert len(context_rows) == 39
    assert {row["expected_reason"] for row in context_rows} == set(gate.CONTEXT_REASONS)


def test_cross_phase_precedence_cases_are_complete() -> None:
    rows = _rows(gate.build_artifacts()[gate.TRUTH_FILE])
    cross = [row for row in rows if row["case_group"] == "cross_phase_precedence"]
    assert len(cross) == 6
    assert [row["expected_reason"] for row in cross[:4]] == [
        gate.MISSING_REASONS[0], gate.TYPE_INVALID_REASONS[0],
        gate.VALUE_INVALID_REASONS[0], gate.CONTEXT_REASONS[0],
    ]


@pytest.mark.parametrize(
    ("status", "http_status"),
    (("failure", 200), ("success", 404), ("success", 500)),
)
def test_failure_status_and_4xx_5xx_pass_admit012(status: str, http_status: int) -> None:
    kwargs = _valid_kwargs()
    kwargs.update(download_result_status=status, observed_http_status=http_status)
    result = gate.classify_admit_012_formal_evaluator_interface_design(**kwargs)
    assert (result.outcome, result.reason, result.passed) == ("passed", "", True)


@pytest.mark.parametrize("case_id", gate.NEGATIVE_RESULT_CASES)
def test_result_contract_negative_cases(case_id: str) -> None:
    baseline = gate.classify_admit_012_formal_evaluator_interface_design(**_valid_kwargs())
    assert gate._assert_negative_result_case(case_id, baseline).startswith("RESULT_CONTRACT_REJECTED:")


def test_issue_transition_preserves_exact16() -> None:
    artifacts = gate.build_artifacts()
    rows = _rows(artifacts[gate.ISSUE_FILE])
    by_id = {row["issue_id"]: row for row in rows}
    assert len(rows) == 16
    assert all(by_id[issue]["status"] == "resolved" for issue in gate.RESOLVED_INTERFACE_ISSUES)
    assert all(by_id[issue]["integration_transition"] == gate.ISSUE_TRANSITION
               for issue in gate.RESOLVED_INTERFACE_ISSUES)
    assert by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] == (
        "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"
    )


def test_readiness_is_exact_and_training_warning_is_preserved() -> None:
    manifest = json.loads(gate.build_artifacts()[gate.MANIFEST_FILE])
    assert all(manifest[flag] is True for flag in gate.TRUE_READINESS)
    assert all(manifest[flag] is False for flag in gate.FALSE_READINESS)
    assert manifest["step12d_status"] == "smoke_legality_only_not_final_training_feature_contract"
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP


def test_no_formal_evaluator_or_result_type_is_defined() -> None:
    assert not hasattr(gate, "evaluate_admit_012")
    assert not hasattr(gate, "Admit012EvaluationResult")


def test_no_adapter_registry_or_dispatcher_is_defined() -> None:
    tree = ast.parse(Path(gate.__file__).read_text())
    top_names = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    assert not any("adapter" in name.lower() or "dispatcher" in name.lower() or name.startswith("register_")
                   for name in top_names)
    assert "EVALUATOR_REGISTRY" not in Path(gate.__file__).read_text()


def test_source_boundary_is_exact30_and_triple_attested() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    assert len(snapshot) == len(gate.SOURCE_PATHS) == 30
    assert all(hashlib.sha256(record.content).hexdigest() == record.sha256 for record in snapshot)
    assert not any(path.startswith("data/raw/") or path.startswith("checkpoints/") for path in gate.SOURCE_PATHS)


def test_deterministic_materialization_and_idempotent_noop(tmp_path: Path) -> None:
    root = tmp_path / gate.STAGE
    first = gate.materialize_contract(root)
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    second = gate.materialize_contract(root)
    after = {path.name: path.read_bytes() for path in root.iterdir()}
    assert first == second and before == after
    assert set(after) == set(gate.OUTPUT_FILES)


def test_materializer_fails_closed_on_existing_mismatch(tmp_path: Path) -> None:
    root = tmp_path / gate.STAGE
    gate.materialize_contract(root)
    (root / gate.CONTRACT_FILE).write_bytes(b"tampered\n")
    with pytest.raises(ValueError, match="existing output set mismatch"):
        gate.materialize_contract(root)


def test_rename_einval_fails_closed_and_cleans_staging(tmp_path: Path) -> None:
    root = tmp_path / gate.STAGE
    with mock.patch.object(gate, "_rename_noreplace", side_effect=OSError(errno.EINVAL, "Invalid argument")):
        with pytest.raises(OSError) as caught:
            gate.materialize_contract(root)
    assert caught.value.errno == errno.EINVAL
    assert not root.exists()
    assert not any(".staging" in path.name for path in tmp_path.iterdir())


def test_checker_rejects_synchronized_semantic_tamper(tmp_path: Path) -> None:
    checker = _load_checker()
    root = tmp_path / gate.STAGE
    shutil.copytree(OUTPUT_ROOT, root)
    contract_path = root / gate.CONTRACT_FILE
    rows = _rows(contract_path.read_bytes())
    rows[0]["source_envelope"] = "candidate_record"
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=gate.CONTRACT_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    contract_path.write_text(stream.getvalue())
    manifest_path = root / gate.MANIFEST_FILE
    manifest = json.loads(manifest_path.read_text())
    manifest["output_sha256"][gate.CONTRACT_FILE] = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(AssertionError):
        checker.validate(root, enforce_frozen_hashes=False)


def test_checker_accepts_exact6_and_frozen_hashes() -> None:
    _load_checker().validate(OUTPUT_ROOT)


@pytest.mark.parametrize("module_path", (Path(gate.__file__), CHECKER_PATH))
def test_imports_are_silent(module_path: Path) -> None:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join((str(ROOT / "src"), str(ROOT / "scripts")))
    module = f"covalent_ext.{module_path.stem}" if module_path.parent.name == "covalent_ext" else module_path.stem
    completed = subprocess.run(
        [sys.executable, "-B", "-c", f"import {module}"], cwd=ROOT,
        env=environment, capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0 and completed.stdout == completed.stderr == ""


def test_exact_output_inventory_and_row_counts() -> None:
    assert OUTPUT_ROOT.is_dir() and {path.name for path in OUTPUT_ROOT.iterdir()} == set(gate.OUTPUT_FILES)
    artifacts = {path.name: path.read_bytes() for path in OUTPUT_ROOT.iterdir()}
    assert (len(_rows(artifacts[gate.CONTRACT_FILE])), len(_rows(artifacts[gate.ROUTING_FILE])),
            len(_rows(artifacts[gate.TRUTH_FILE])), len(_rows(artifacts[gate.SOURCE_FILE])),
            len(_rows(artifacts[gate.ISSUE_FILE]))) == (70, 27, 105, 30, 16)


def test_no_forbidden_stage_artifacts_or_unexpected_changes() -> None:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".tmp", ".part", ".pyc"}
    stage_files = {path.relative_to(ROOT).as_posix() for path in OUTPUT_ROOT.rglob("*") if path.is_file()}
    assert not any(path.suffix in forbidden for path in OUTPUT_ROOT.rglob("*") if path.is_file())
    assert stage_files == {f"{gate.DEFAULT_OUTPUT_ROOT.as_posix()}/{name}" for name in gate.OUTPUT_FILES}
    status = subprocess.run(["git", "status", "--porcelain=v1"], cwd=ROOT, capture_output=True, text=True, check=True)
    changed = {line[3:].rstrip("/") for line in status.stdout.splitlines()}
    assert changed <= AUTHORIZED_FILES | {gate.DEFAULT_OUTPUT_ROOT.as_posix()}
