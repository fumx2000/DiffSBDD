"""Targeted tests for the pure ADMIT_013 standalone evaluator."""

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
from dataclasses import fields
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_design_gate as design,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_013_rule_logic_interface as implementation,
)


ROOT = Path(__file__).resolve().parents[1]
BASE = "79e63dce368722b126ad21208a3de13f7ea4b6df"
PARENT = "2eea08835c4ef88d5b810509134f8eef94e3e99e"
TREE = "ac3633abc2cf52a715faf36faea827f76d4236d9"
SUBJECT = "add CovaPIE ADMIT_013 formal evaluator interface contract v1"
SHA_A = "0123456789abcdef" * 4
SHA_B = "abcdef0123456789" * 4
TRUTH_PATH = ROOT / (
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/"
    "covapie_admit_013_formal_evaluator_interface_truth_matrix.csv"
)
CHECKER_PATH = ROOT / (
    "scripts/check_covapie_bulk_download_admission_admit_013_rule_logic_interface_v1.py"
)


def _valid(**changes):
    values = {
        "download_result_status": "success",
        "observed_http_status": 200,
        "observed_content_length_bytes": 10,
        "observed_sha256": SHA_A,
        "expected_sha256": SHA_A,
    }
    values.update(changes)
    return values


def _load_checker():
    spec = importlib.util.spec_from_file_location("admit013_checker", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _csv_payload(rows, fieldnames):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _mutate_csv_payload(payloads, name, mutation):
    changed = dict(payloads)
    reader = csv.DictReader(io.StringIO(changed[name].decode(), newline=""))
    fieldnames = tuple(reader.fieldnames or ())
    rows = list(reader)
    mutation(rows)
    changed[name] = _csv_payload(rows, fieldnames)
    return changed


def _write_synthetic_outputs(root, checker):
    root.mkdir(parents=True)
    for name in checker.OUTPUT_FILES:
        (root / name).write_bytes((name + "\n").encode())


def _run_git(repo, *arguments, input_text=None):
    return subprocess.run(
        ["git", *arguments],
        cwd=repo,
        input=input_text,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def _initialize_synthetic_repo(repo, checker):
    repo.mkdir()
    _run_git(repo, "init", "-q")
    _run_git(repo, "config", "user.name", "CovaPIE test")
    _run_git(repo, "config", "user.email", "covapie-test@example.invalid")
    (repo / ".gitignore").write_text(".pytest_cache/\n__pycache__/\n*.pyc\n")
    (repo / "README.md").write_text("synthetic lifecycle repository\n")
    for directory in checker.STAGE_TOP_LEVEL_DIRECTORIES:
        (repo / directory).mkdir(parents=True, exist_ok=True)
    _run_git(repo, "add", "--", ".gitignore", "README.md")
    _run_git(repo, "commit", "-q", "-m", "synthetic base")
    return _run_git(repo, "rev-parse", "HEAD")


def _write_synthetic_stage(repo, checker):
    for path in checker.STAGE_PATHS:
        absolute = repo / path
        absolute.parent.mkdir(parents=True, exist_ok=True)
        absolute.write_text(path.as_posix() + "\n")


class _TestStrSubclass(str):
    pass


class _TestTupleSubclass(tuple):
    pass


class _TestPairSubclass(tuple):
    pass


class _TestResultSubclass(implementation.Admit013EvaluationResult):
    pass


def _test_local_validate_result(value):
    if type(value) is dict:
        if tuple(value) != implementation.RESULT_FIELDS:
            raise ValueError("test-local result mapping field order drift")
        raise TypeError("test-local exact dataclass storage required")
    if type(value) is not implementation.Admit013EvaluationResult:
        raise TypeError("test-local exact result type required")
    return implementation.Admit013EvaluationResult(
        *(getattr(value, name) for name in implementation.RESULT_FIELDS)
    )


def _test_local_negative_result(case_id, baseline):
    values = {name: getattr(baseline, name) for name in implementation.RESULT_FIELDS}
    download = baseline.canonical_download_result_record
    if case_id == "WRONG_TOP_LEVEL_RESULT_TYPE":
        return _test_local_validate_result(object())
    if case_id == "RESULT_SUBCLASS":
        return _TestResultSubclass(
            *(values[name] for name in implementation.RESULT_FIELDS)
        )
    if case_id in {"STORAGE_NOT_EXACT_DATACLASS", "MISSING_FIELD", "EXTRA_FIELD"}:
        mapping = dict(values)
        if case_id == "MISSING_FIELD":
            mapping.pop("reason")
        elif case_id == "EXTRA_FIELD":
            mapping["extra"] = True
        return _test_local_validate_result(mapping)
    if case_id == "FIELD_REORDER":
        reordered = {"outcome": values["outcome"]}
        reordered.update((name, values[name]) for name in implementation.RESULT_FIELDS if name != "outcome")
        return _test_local_validate_result(reordered)
    if case_id == "PASSED_INT_ONE":
        values["passed"] = 1
    elif case_id == "BLOCKS_INT_ZERO":
        values["blocks_candidate"] = 0
    elif case_id == "CANONICAL_OUTER_LIST":
        values["canonical_download_result_record"] = list(download)
    elif case_id == "MALFORMED_PAIR":
        values["canonical_download_result_record"] = ((implementation.DOWNLOAD_FIELDS[0],), *download[1:])
    elif case_id == "PAIR_LIST":
        values["canonical_download_result_record"] = (list(download[0]), *download[1:])
    elif case_id == "PAIR_SUBCLASS":
        values["canonical_download_result_record"] = (_TestPairSubclass(download[0]), *download[1:])
    elif case_id == "TUPLE_SUBCLASS":
        values["canonical_download_result_record"] = _TestTupleSubclass(download)
    elif case_id == "WRONG_PAIR_NAME":
        values["canonical_download_result_record"] = (("wrong", download[0][1]), *download[1:])
    elif case_id == "WRONG_PAIR_ORDER":
        values["canonical_download_result_record"] = tuple(reversed(download))
    elif case_id == "DUPLICATE_PAIR":
        values["canonical_download_result_record"] = (download[0], download[0], *download[2:])
    elif case_id == "EXTRA_PAIR":
        values["canonical_download_result_record"] = (*download, ("extra", "value"))
    elif case_id == "CANONICAL_AUTHORITY_CONTAINS_MISSING_FIELD":
        values["canonical_integrity_authority_record"] = (
            (implementation.AUTHORITY_FIELDS[0], implementation._MISSING),
        )
        values["validated_integrity_authority_fields"] = (implementation.AUTHORITY_FIELDS[0],)
    elif case_id == "VALIDATED_TUPLE_LIST":
        values["validated_download_result_fields"] = list(implementation.DOWNLOAD_FIELDS)
    elif case_id == "CONSUMED_TUPLE_LIST":
        values["consumed_download_result_fields"] = list(implementation.DOWNLOAD_FIELDS)
    elif case_id == "VALIDATED_NAME_NOT_EXACT_STR":
        values["validated_download_result_fields"] = (
            _TestStrSubclass(implementation.DOWNLOAD_FIELDS[0]),
            *implementation.DOWNLOAD_FIELDS[1:],
        )
    elif case_id == "CONSUMED_NAME_NOT_EXACT_STR":
        values["consumed_integrity_authority_fields"] = (
            _TestStrSubclass(implementation.AUTHORITY_FIELDS[0]),
            *implementation.AUTHORITY_FIELDS[1:],
        )
    elif case_id == "DESIGN_SENTINEL_LEAK":
        values["canonical_download_result_record"] = (
            (implementation.DOWNLOAD_FIELDS[0], implementation._MISSING),
            *download[1:],
        )
    elif case_id == "EVALUATOR_IO_TRUE":
        values["evaluator_io_used"] = True
    elif case_id == "OUTCOME_REASON_INVARIANT_CONFLICT":
        values.update(outcome="blocked", passed=False, blocks_candidate=True, reason="")
    elif case_id == "ADMISSION_RULE_ID_DRIFT":
        values["admission_rule_id"] = "ADMIT_012"
    else:
        raise AssertionError(f"unhandled test-local negative case: {case_id}")
    return implementation.Admit013EvaluationResult(
        *(values[name] for name in implementation.RESULT_FIELDS)
    )


def test_base_identity_and_ancestor_policy():
    observed = subprocess.run(
        ["git", "show", "-s", "--format=%H%n%P%n%T%n%s", BASE],
        cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.splitlines()
    assert observed == [BASE, PARENT, TREE, SUBJECT]
    assert subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE, "HEAD"], cwd=ROOT
    ).returncode == 0


def test_canonical_runtime_identity_and_clear_noncanonical_rejection():
    checker = _load_checker()
    for module in (implementation, checker):
        module._validate_canonical_evidence_runtime_identity("cpython", (3, 10, 4))
        for observed_implementation, observed_version in (
            ("cpython", (3, 12, 9)),
            ("pypy", (3, 10, 4)),
        ):
            with pytest.raises(RuntimeError) as captured:
                module._validate_canonical_evidence_runtime_identity(
                    observed_implementation,
                    observed_version,
                )
            message = str(captured.value)
            assert "required: CPython 3.10.4" in message
            assert f"observed implementation: {observed_implementation}" in message
            assert "observed version:" in message
            assert "frozen AST evidence is version-sensitive" in message
            assert "evaluator-only semantic smoke" in message


def test_runtime_guard_is_evidence_only_and_precedes_build_checker(
    tmp_path,
    monkeypatch,
):
    def reject_noncanonical():
        raise RuntimeError("synthetic noncanonical evidence rejection")

    monkeypatch.setattr(
        implementation,
        "_assert_canonical_evidence_runtime",
        reject_noncanonical,
    )
    assert implementation.evaluate_admit_013(**_valid()).passed is True
    with pytest.raises(RuntimeError, match="synthetic noncanonical"):
        implementation._formal_source_attestation()
    with pytest.raises(RuntimeError, match="synthetic noncanonical"):
        implementation.build_artifacts(snapshot=())
    with pytest.raises(RuntimeError, match="synthetic noncanonical"):
        implementation.materialize_contract(tmp_path / "forbidden-evidence")

    checker = _load_checker()
    monkeypatch.setattr(
        checker,
        "_assert_canonical_evidence_runtime",
        reject_noncanonical,
    )
    with pytest.raises(RuntimeError, match="synthetic noncanonical"):
        checker.check()


def test_public_signature_is_exact_seven_keyword_only():
    signature = inspect.signature(implementation.evaluate_admit_013)
    assert tuple(signature.parameters) == implementation.PARAMETERS
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert all(
        parameter.default is implementation._MISSING
        for parameter in signature.parameters.values()
    )
    assert signature.return_annotation is implementation.Admit013EvaluationResult
    with pytest.raises(TypeError):
        implementation.evaluate_admit_013("success")


def test_private_missing_singleton_and_falsey_values_are_distinct():
    assert implementation._MISSING is implementation._MISSING
    assert type(implementation._MISSING).__name__ == "_MissingAdmit013Value"
    assert "_MISSING" not in implementation.__all__ if hasattr(implementation, "__all__") else True
    missing = implementation.evaluate_admit_013()
    assert missing.reason == "DOWNLOAD_RESULT_STATUS_MISSING"
    for value in (None, False, 0, ""):
        observed = implementation.evaluate_admit_013(download_result_status=value)
        assert observed.reason == "OBSERVED_HTTP_STATUS_MISSING"
    for value in (None, False, 0, ""):
        observed = implementation.evaluate_admit_013(**_valid(expected_sha256=value))
        assert observed.reason != "INTEGRITY_AUTHORITY_MISSING"


@pytest.mark.parametrize(
    ("missing_name", "reason", "validated", "consumed"),
    [
        ("download_result_status", "DOWNLOAD_RESULT_STATUS_MISSING", (), ("download_result_status",)),
        ("observed_http_status", "OBSERVED_HTTP_STATUS_MISSING", implementation.DOWNLOAD_FIELDS[:1], implementation.DOWNLOAD_FIELDS[:2]),
        ("observed_content_length_bytes", "OBSERVED_CONTENT_LENGTH_BYTES_MISSING", implementation.DOWNLOAD_FIELDS[:2], implementation.DOWNLOAD_FIELDS[:3]),
        ("observed_sha256", "OBSERVED_SHA256_MISSING", implementation.DOWNLOAD_FIELDS[:3], implementation.DOWNLOAD_FIELDS),
    ],
)
def test_exact4_presence_precedence(missing_name, reason, validated, consumed):
    kwargs = _valid()
    kwargs.pop(missing_name)
    kwargs["expected_content_length_bytes"] = None
    observed = implementation.evaluate_admit_013(**kwargs)
    assert observed.outcome == "blocked" and observed.reason == reason
    assert observed.canonical_download_result_record == ()
    assert observed.canonical_integrity_authority_record == ()
    assert observed.validated_download_result_fields == validated
    assert observed.consumed_download_result_fields == consumed
    assert observed.consumed_integrity_authority_fields == ()


@pytest.mark.parametrize(
    ("changes", "reason", "validated"),
    [
        ({"download_result_status": None}, "DOWNLOAD_RESULT_STATUS_TYPE_INVALID", ()),
        ({"download_result_status": "SUCCESS"}, "DOWNLOAD_RESULT_STATUS_VALUE_INVALID", ()),
        ({"observed_http_status": True}, "OBSERVED_HTTP_STATUS_TYPE_INVALID", implementation.DOWNLOAD_FIELDS[:1]),
        ({"observed_http_status": 600}, "OBSERVED_HTTP_STATUS_RANGE_INVALID", implementation.DOWNLOAD_FIELDS[:1]),
        ({"observed_content_length_bytes": False}, "OBSERVED_CONTENT_LENGTH_BYTES_TYPE_INVALID", implementation.DOWNLOAD_FIELDS[:2]),
        ({"observed_content_length_bytes": -1}, "OBSERVED_CONTENT_LENGTH_BYTES_RANGE_INVALID", implementation.DOWNLOAD_FIELDS[:2]),
        ({"observed_sha256": SHA_A.encode()}, "OBSERVED_SHA256_TYPE_INVALID", implementation.DOWNLOAD_FIELDS[:3]),
        ({"observed_sha256": SHA_A.upper()}, "OBSERVED_SHA256_FORMAT_INVALID", implementation.DOWNLOAD_FIELDS[:3]),
    ],
)
def test_exact4_type_then_value_precedence(changes, reason, validated):
    kwargs = _valid(**changes)
    kwargs["expected_content_length_bytes"] = None
    observed = implementation.evaluate_admit_013(**kwargs)
    assert observed.outcome == "invalid" and observed.reason == reason
    assert observed.validated_download_result_fields == validated
    assert observed.consumed_download_result_fields == implementation.DOWNLOAD_FIELDS
    assert observed.consumed_integrity_authority_fields == ()


def test_optional_authority_and_consumed_prefix_semantics():
    observed = implementation.evaluate_admit_013(
        **_valid(expected_content_length_bytes=implementation._MISSING, expected_sha256=None)
    )
    assert observed.reason == "EXPECTED_SHA256_TYPE_INVALID"
    assert observed.canonical_integrity_authority_record == ()
    assert observed.validated_integrity_authority_fields == ()
    assert observed.consumed_integrity_authority_fields == implementation.AUTHORITY_FIELDS[:2]
    observed = implementation.evaluate_admit_013(
        **_valid(expected_content_length_bytes=10, explicit_integrity_verdict=None)
    )
    assert observed.reason == "EXPLICIT_INTEGRITY_VERDICT_TYPE_INVALID"
    assert observed.canonical_integrity_authority_record == (
        ("expected_content_length_bytes", 10), ("expected_sha256", SHA_A),
    )
    assert observed.consumed_integrity_authority_fields == implementation.AUTHORITY_FIELDS


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"download_result_status": "failure", "observed_http_status": 500, "observed_content_length_bytes": 0, "expected_sha256": SHA_B, "explicit_integrity_verdict": "failed", "expected_content_length_bytes": 11}, "DOWNLOAD_RESULT_STATUS_FAILURE"),
        ({"observed_http_status": 500, "observed_content_length_bytes": 0, "expected_sha256": SHA_B}, "OBSERVED_HTTP_STATUS_NOT_SUCCESS"),
        ({"observed_content_length_bytes": 0, "expected_sha256": SHA_B}, "OBSERVED_CONTENT_EMPTY"),
        ({"expected_sha256": SHA_B, "explicit_integrity_verdict": "failed", "expected_content_length_bytes": 11}, "OBSERVED_SHA256_MISMATCH"),
        ({"explicit_integrity_verdict": "failed", "expected_content_length_bytes": 11}, "EXPLICIT_INTEGRITY_VERDICT_FAILED"),
        ({"expected_content_length_bytes": 11}, "OBSERVED_CONTENT_LENGTH_MISMATCH"),
        ({"expected_sha256": implementation._MISSING, "expected_content_length_bytes": 10}, "INTEGRITY_AUTHORITY_MISSING"),
    ],
)
def test_exact7_business_precedence(changes, reason):
    observed = implementation.evaluate_admit_013(**_valid(**changes))
    assert observed.outcome == "blocked"
    assert observed.reason == reason
    assert observed.consumed_integrity_authority_fields == implementation.AUTHORITY_FIELDS


@pytest.mark.parametrize(
    ("http_status", "outcome"),
    [(100, "blocked"), (199, "blocked"), (200, "passed"), (299, "passed"), (300, "blocked"), (599, "blocked")],
)
def test_http_business_boundaries(http_status, outcome):
    assert implementation.evaluate_admit_013(**_valid(observed_http_status=http_status)).outcome == outcome


def test_strong_authority_and_conflict_rules():
    expected_length_only = implementation.evaluate_admit_013(
        **_valid(expected_sha256=implementation._MISSING, expected_content_length_bytes=10)
    )
    assert expected_length_only.reason == "INTEGRITY_AUTHORITY_MISSING"
    assert implementation.evaluate_admit_013(**_valid(expected_sha256=SHA_A)).passed is True
    assert implementation.evaluate_admit_013(
        **_valid(expected_sha256=implementation._MISSING, explicit_integrity_verdict="verified")
    ).passed is True
    conflict = implementation.evaluate_admit_013(
        **_valid(expected_sha256=SHA_B, explicit_integrity_verdict="verified")
    )
    assert conflict.reason == "OBSERVED_SHA256_MISMATCH"
    conflict = implementation.evaluate_admit_013(
        **_valid(expected_sha256=SHA_A, explicit_integrity_verdict="failed")
    )
    assert conflict.reason == "EXPLICIT_INTEGRITY_VERDICT_FAILED"


def test_exact12_frozen_result_and_top_level_types():
    result = implementation.evaluate_admit_013(**_valid())
    assert tuple(field.name for field in fields(result)) == implementation.RESULT_FIELDS
    assert type(result.admission_rule_id) is str
    assert type(result.outcome) is str
    assert type(result.passed) is bool
    assert type(result.blocks_candidate) is bool
    assert type(result.reason) is str
    assert all(type(getattr(result, name)) is tuple for name in implementation.RESULT_FIELDS[5:11])
    assert type(result.evaluator_io_used) is bool and result.evaluator_io_used is False
    with pytest.raises(Exception):
        result.reason = "changed"


def test_exact26_result_negative_projection_rejected():
    baseline = implementation.evaluate_admit_013(**_valid())
    assert len(implementation.NEGATIVE_RESULT_CASES) == 26
    for case_id in implementation.NEGATIVE_RESULT_CASES:
        with pytest.raises((TypeError, ValueError), match=".+"):
            _test_local_negative_result(case_id, baseline)


def test_actual_evaluator_equals_committed_design_oracle_exact102_and_business23():
    rows = list(csv.DictReader(TRUTH_PATH.open(newline="")))
    representation_columns = tuple(f"{name}_representation" for name in implementation.PARAMETERS)
    compared = 0
    business = 0
    for row in rows:
        if row["case_id"] in implementation.NEGATIVE_RESULT_CASES:
            continue
        actual_values = tuple(
            implementation._decode_representation(row[column]) for column in representation_columns
        )
        design_values = tuple(
            design._DESIGN_MISSING if value is implementation._MISSING else value
            for value in actual_values
        )
        actual = implementation.evaluate_admit_013(
            **dict(zip(implementation.PARAMETERS, actual_values, strict=True))
        )
        oracle = design.classify_admit_013_formal_evaluator_interface_design(
            **dict(zip(design.PARAMETERS, design_values, strict=True))
        )
        actual_tuple = tuple(getattr(actual, name) for name in implementation.RESULT_FIELDS)
        oracle_tuple = tuple(getattr(oracle, name) for name in design.RESULT_FIELDS)
        assert actual_tuple == oracle_tuple, row["case_id"]
        assert all(type(left) is type(right) for left, right in zip(actual_tuple, oracle_tuple, strict=True))
        compared += 1
        business += row["case_group"] == "inherited_exact7_business_projection"
    assert compared == 102 and business == 23


def test_evaluator_is_deterministic_and_does_not_touch_io(monkeypatch):
    expected = implementation.evaluate_admit_013(**_valid())
    monkeypatch.setattr("builtins.open", lambda *args, **kwargs: pytest.fail("I/O used"))
    assert implementation.evaluate_admit_013(**_valid()) == expected


def test_formal_marker_ast_hashes_and_purity_evidence():
    source, full_sha, prefix_sha, digests = implementation._formal_source_attestation()
    manifest = json.loads(implementation.build_artifacts()[implementation.MANIFEST_FILE])
    original_nine = {
        "evaluate_admit_013": "0b42e4c6e4d51e1b60a39af66d42ba3b0a86c5daa3e088bec1dbabb4995eb91f",
        "_make_result": "6c404d01cde2b88b4103996606421f975087dcc15fbdf6ac67985a8b9a109379",
        "_business_reason": "eb714b15ae11489501c7e6c3bc96fd8b66c2f926784a1870d67f6329ef68af52",
        "Admit013EvaluationResult": "30793fc44c5522e9408241349b1801e8591bdb21fe5f8008238dd0bee59ae113",
        "Admit013EvaluationResult.__post_init__": "5d3d041f10e11e204d5eb0e9b2ff754a4b71d6bff801c63603de85c2fd6ae2d5",
        "_download_value_valid": "5da80ba5d90e13579caca05cc291d05a05e7be4e080d486a557f371ce4bfc815",
        "_authority_value_valid": "ff60eb0868bdc31784cc8be92e05260a170b39f654092513c3166199faea0919",
        "_pair_record_shape_valid": "6aaa58c523af2eaf7e1b23560ee2977cbbbe2d7967d6f4f6a4879ebff625b1ef",
        "_name_tuple_valid": "8428ddcce209873193f9cc59690ed9ac915f6811e3b685ca5107cfcd6014a030",
    }
    assert implementation.FORMAL_CLOSURE == (
        *original_nine,
        "_MissingAdmit013Value",
    )
    assert len(implementation.FORMAL_CLOSURE) == 10
    assert {name: digests[name] for name in original_nine} == original_nine
    assert digests["_MissingAdmit013Value"] == (
        "036c3099407e7a052d48a6a6dc37b269b41c7144bfe52a0c1e96eb623944ca0b"
    )
    assert source and full_sha == manifest["formal_production_sha256"]
    assert prefix_sha == manifest["formal_marker_prefix_sha256"] == (
        "e5b6e3e51022b342f022f38a498d7b64e7b882382ea887260d34acf9ea0e00c2"
    )
    assert digests == manifest["formal_ast_sha256"]
    assert manifest["formal_closure_count"] == 10
    assert manifest["formal_closure"] == list(implementation.FORMAL_CLOSURE)
    assert source.decode().count(implementation.FORMAL_MARKER) == 1


def test_deterministic_build_issue_identity_and_readiness():
    first = implementation.build_artifacts()
    second = implementation.build_artifacts()
    assert first == second
    issue_source = (
        ROOT / implementation.DESIGN_STAGE /
        "covapie_admit_013_formal_evaluator_interface_issue_readiness_inventory.csv"
    ).read_bytes()
    assert first[implementation.ISSUE_FILE] == issue_source
    manifest = json.loads(first[implementation.MANIFEST_FILE])
    assert manifest["row_counts"]["formal_contract"] == 76
    assert manifest["row_counts"]["truth_matrix"] == 128
    assert manifest["row_counts"]["purity_audit"] == 16
    assert manifest["row_counts"]["inherited_business_projection"] == 23
    assert manifest["row_counts"]["result_negative_projection"] == 26
    assert manifest["issue_transition_count"] == 0
    assert manifest["readiness"]["ready_for_admit_013_unified_adapter_contract_design"] is True
    assert manifest["readiness"]["admit_013_registered_in_engine"] is False
    assert manifest["readiness"]["ready_for_training"] is False
    assert manifest["canonical_evidence_python_implementation"] == "cpython"
    assert manifest["canonical_evidence_python_version"] == "3.10.4"
    assert manifest["ast_attestation_cross_python_version_portable"] is False
    assert manifest["noncanonical_python_policy"] == (
        "evaluator_semantic_smoke_only; artifact_build_checker_and_frozen_ast_forbidden"
    )
    assert manifest["python_runtime_migration_policy"] == (
        "explicit_contract_refresh_required"
    )
    assert manifest["recommended_next_step"] == "design_covapie_admit_013_unified_adapter_contract_v1"


def test_materializer_exact_set_noop_and_mismatch_fail_closed(tmp_path):
    output = tmp_path / "evidence"
    implementation.materialize_contract(output)
    before = {entry.name: entry.stat().st_ino for entry in output.iterdir()}
    implementation.materialize_contract(output)
    after = {entry.name: entry.stat().st_ino for entry in output.iterdir()}
    assert before == after
    leaf = output / implementation.CONTRACT_FILE
    leaf.write_bytes(leaf.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match="existing output set mismatch"):
        implementation.materialize_contract(output)


def test_gpfs_einval_fails_closed_without_residue(tmp_path, monkeypatch):
    output = tmp_path / "evidence"

    def fail_rename(*_args):
        raise OSError(errno.EINVAL, "Invalid argument")

    monkeypatch.setattr(implementation, "_rename_noreplace", fail_rename)
    with pytest.raises(OSError) as captured:
        implementation.materialize_contract(output)
    assert captured.value.errno == errno.EINVAL
    assert not output.exists()
    assert not tuple(tmp_path.glob(".*.staging"))


def test_no_adapter_registry_exact13_or_training_change():
    source = (ROOT / implementation.PRODUCTION_PATH if hasattr(implementation, "PRODUCTION_PATH") else ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_013_rule_logic_interface.py").read_text()
    prefix = source.split(implementation.FORMAL_MARKER, 1)[0]
    assert "EVALUATOR_REGISTRY" not in prefix
    assert "prior_admit_012_result" not in prefix
    assert "classify_admit_013_formal_evaluator_interface_design" not in prefix
    runtime = json.loads((ROOT / "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_runtime_manifest.json").read_text())
    assert runtime["registered_rule_count"] == 12
    assert "ADMIT_013" in runtime["known_not_registered_rule_ids"]


@pytest.fixture(scope="module")
def checker_evidence():
    checker = _load_checker()
    sources, source_modes = checker._check_base_and_sources()
    _, ast_digests = checker._check_formal_source()
    payloads = implementation.build_artifacts()
    return checker, payloads, sources, source_modes, ast_digests


def test_checker_pinned_output_rejects_root_and_leaf_symlinks(tmp_path):
    checker = _load_checker()
    target = tmp_path / "target"
    _write_synthetic_outputs(target, checker)
    root_link = tmp_path / "root-link"
    root_link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="unsafe output root"):
        checker._read_pinned_output_payloads(root_link)

    root = tmp_path / "leaf-root"
    _write_synthetic_outputs(root, checker)
    leaf = root / checker.OUTPUT_FILES[0]
    leaf.unlink()
    leaf.symlink_to(tmp_path / "outside")
    with pytest.raises(ValueError, match="unsafe output leaf"):
        checker._read_pinned_output_payloads(root)


@pytest.mark.parametrize("inventory_change", ["extra", "missing"])
def test_checker_pinned_output_rejects_inventory_drift(tmp_path, inventory_change):
    checker = _load_checker()
    root = tmp_path / "evidence"
    _write_synthetic_outputs(root, checker)
    if inventory_change == "extra":
        (root / "extra.csv").write_text("extra\n")
    else:
        (root / checker.OUTPUT_FILES[-1]).unlink()
    with pytest.raises(ValueError, match="Exact6 output inventory drift"):
        checker._read_pinned_output_payloads(root)


def test_checker_pinned_output_rejects_leaf_identity_drift(tmp_path, monkeypatch):
    checker = _load_checker()
    root = tmp_path / "evidence"
    _write_synthetic_outputs(root, checker)
    original = checker._read_output_leaf_at
    changed = False

    def replace_after_read(root_fd, name, identity):
        nonlocal changed
        data = original(root_fd, name, identity)
        if not changed:
            changed = True
            target = root / name
            replacement = root / "replacement.tmp"
            replacement.write_bytes(data)
            os.replace(replacement, target)
        return data

    monkeypatch.setattr(checker, "_read_output_leaf_at", replace_after_read)
    with pytest.raises(ValueError, match="identity drift"):
        checker._read_pinned_output_payloads(root)


def test_checker_pinned_output_rejects_root_identity_drift(tmp_path, monkeypatch):
    checker = _load_checker()
    root = tmp_path / "evidence"
    relocated = tmp_path / "relocated"
    _write_synthetic_outputs(root, checker)
    original = checker._read_output_leaf_at
    changed = False

    def replace_root_after_read(root_fd, name, identity):
        nonlocal changed
        data = original(root_fd, name, identity)
        if not changed:
            changed = True
            root.rename(relocated)
            root.mkdir()
        return data

    monkeypatch.setattr(checker, "_read_output_leaf_at", replace_root_after_read)
    with pytest.raises((FileNotFoundError, ValueError), match="identity drift|No such file"):
        checker._read_pinned_output_payloads(root)


def test_checker_leaf_open_is_pinned_to_root_dir_fd(tmp_path, monkeypatch):
    checker = _load_checker()
    root = tmp_path / "evidence"
    _write_synthetic_outputs(root, checker)
    real_open = os.open
    leaf_calls = []

    def observed_open(path, flags, *args, **kwargs):
        if isinstance(path, str) and path in checker.OUTPUT_FILES:
            leaf_calls.append((path, flags, kwargs.get("dir_fd")))
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(checker.os, "open", observed_open)
    checker._read_pinned_output_payloads(root)
    assert [name for name, _, _ in leaf_calls] == list(checker.OUTPUT_FILES)
    assert all(type(root_fd) is int for _, _, root_fd in leaf_calls)
    assert all(flags & os.O_NOFOLLOW and flags & os.O_CLOEXEC for _, flags, _ in leaf_calls)


def test_checker_runtime_and_source_lineage_precede_output_read(monkeypatch):
    checker = _load_checker()
    events = []
    monkeypatch.setattr(
        checker,
        "_assert_canonical_evidence_runtime",
        lambda: events.append("runtime"),
    )
    monkeypatch.setattr(
        checker,
        "_check_base_and_sources",
        lambda: (events.append("source_lineage") or ({}, {})),
    )
    monkeypatch.setattr(
        checker,
        "_check_formal_source",
        lambda: (events.append("formal_source") or (b"source", {})),
    )
    monkeypatch.setattr(
        checker,
        "_check_outputs",
        lambda *_args: (
            events.append("output_read")
            or {"recommended_next_step": "design_covapie_admit_013_unified_adapter_contract_v1"}
        ),
    )
    monkeypatch.setattr(
        checker,
        "_check_lifecycle",
        lambda: (events.append("lifecycle") or "pre_commit"),
    )
    checker.check()
    assert events == [
        "runtime",
        "source_lineage",
        "formal_source",
        "output_read",
        "lifecycle",
    ]


@pytest.mark.parametrize(
    "section",
    ["signature_parameter", "reason_vocabulary", "validation_phase", "result_field"],
)
def test_checker_rejects_ordered_contract_semantic_tamper(checker_evidence, section):
    checker, payloads, sources, source_modes, ast_digests = checker_evidence

    def reorder(rows):
        selected = [row for row in rows if row["contract_section"] == section]
        selected[0]["public_name"], selected[1]["public_name"] = (
            selected[1]["public_name"],
            selected[0]["public_name"],
        )

    tampered = _mutate_csv_payload(payloads, checker.OUTPUT_FILES[0], reorder)
    with pytest.raises(ValueError, match="implementation contract drift"):
        checker._validate_output_semantics(
            tampered,
            sources,
            source_modes,
            ast_digests,
        )


@pytest.mark.parametrize(
    "semantic_case",
    ["zero_content_pass", "expected_length_alone_pass"],
)
def test_checker_rejects_business_semantic_weakening(checker_evidence, semantic_case):
    checker, payloads, sources, source_modes, ast_digests = checker_evidence

    def weaken(rows):
        passed = next(
            row["observed_formal_result"]
            for row in rows
            if "'passed', True, False, ''" in row["observed_formal_result"]
        )
        if semantic_case == "zero_content_pass":
            target = next(
                row for row in rows
                if "OBSERVED_CONTENT_EMPTY" in row["observed_formal_result"]
            )
        else:
            target = next(
                row for row in rows
                if "INTEGRITY_AUTHORITY_MISSING" in row["observed_formal_result"]
                and row["expected_content_length_bytes_representation"] == "10"
                and row["expected_sha256_representation"] == "<MISSING>"
                and row["explicit_integrity_verdict_representation"] == "<MISSING>"
            )
        target["observed_formal_result"] = passed

    tampered = _mutate_csv_payload(payloads, checker.OUTPUT_FILES[1], weaken)
    with pytest.raises(ValueError, match="independent oracle mismatch"):
        checker._validate_output_semantics(
            tampered,
            sources,
            source_modes,
            ast_digests,
        )


def test_checker_rejects_purity_row_tamper(checker_evidence):
    checker, payloads, sources, source_modes, ast_digests = checker_evidence
    tampered = _mutate_csv_payload(
        payloads,
        checker.OUTPUT_FILES[3],
        lambda rows: rows[0].update(mutation_absent="false"),
    )
    with pytest.raises(ValueError, match="purity evidence drift"):
        checker._validate_output_semantics(tampered, sources, source_modes, ast_digests)


@pytest.mark.parametrize("field", ["base_tree_mode", "filesystem_sha256"])
def test_checker_rejects_source_audit_mode_and_sha_tamper(checker_evidence, field):
    checker, payloads, sources, source_modes, ast_digests = checker_evidence

    def mutate(rows):
        rows[0][field] = "100755" if field == "base_tree_mode" else "0" * 64

    tampered = _mutate_csv_payload(payloads, checker.OUTPUT_FILES[2], mutate)
    with pytest.raises(ValueError, match="source boundary evidence drift"):
        checker._validate_output_semantics(tampered, sources, source_modes, ast_digests)


@pytest.mark.parametrize("tamper_kind", ["missing", "extra", "reorder"])
def test_checker_rejects_manifest_key_tamper(checker_evidence, tamper_kind):
    checker, payloads, sources, source_modes, ast_digests = checker_evidence
    tampered = dict(payloads)
    manifest = json.loads(tampered[checker.OUTPUT_FILES[5]])
    if tamper_kind == "missing":
        manifest.pop("project")
        data = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    elif tamper_kind == "extra":
        manifest["unexpected"] = True
        data = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    else:
        manifest = dict(reversed(tuple(manifest.items())))
        data = json.dumps(manifest, indent=2, sort_keys=False) + "\n"
    tampered[checker.OUTPUT_FILES[5]] = data.encode()
    with pytest.raises(ValueError, match="manifest exact top-level keys/order drift"):
        checker._validate_output_semantics(tampered, sources, source_modes, ast_digests)


def test_checker_rejects_synchronized_csv_and_manifest_tamper(checker_evidence):
    checker, payloads, sources, source_modes, ast_digests = checker_evidence

    def weaken(rows):
        rows[0]["public_name"] = rows[1]["public_name"]

    tampered = _mutate_csv_payload(payloads, checker.OUTPUT_FILES[0], weaken)
    manifest = json.loads(tampered[checker.OUTPUT_FILES[5]])
    manifest["output_sha256"][checker.OUTPUT_FILES[0]] = hashlib.sha256(
        tampered[checker.OUTPUT_FILES[0]]
    ).hexdigest()
    tampered[checker.OUTPUT_FILES[5]] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    with pytest.raises(ValueError, match="implementation contract drift"):
        checker._validate_output_semantics(tampered, sources, source_modes, ast_digests)


@pytest.mark.parametrize(
    ("scenario", "expected"),
    [
        ("base_untracked", "pre_commit"),
        ("descendant_unrelated_commit", "pre_commit"),
        ("tracked_clean", "post_commit"),
        ("unrelated_noise", "pre_commit"),
        ("mixed", None),
        ("stage_path_staged", None),
        ("tracked_dirty", None),
        ("missing", None),
        ("ignored", None),
        ("extra_output", None),
        ("extra_top_level", None),
        ("nonancestor", None),
    ],
)
def test_exact10_lifecycle_synthetic_repository(
    tmp_path,
    monkeypatch,
    scenario,
    expected,
):
    checker = _load_checker()
    repo = tmp_path / "repo"
    base = _initialize_synthetic_repo(repo, checker)
    if scenario == "descendant_unrelated_commit":
        (repo / "unrelated-commit.txt").write_text("unrelated\n")
        _run_git(repo, "add", "--", "unrelated-commit.txt")
        _run_git(repo, "commit", "-q", "-m", "unrelated descendant")
    _write_synthetic_stage(repo, checker)

    exact_paths = [path.as_posix() for path in checker.STAGE_PATHS]
    if scenario == "tracked_clean":
        _run_git(repo, "add", "--", *exact_paths)
        _run_git(repo, "commit", "-q", "-m", "track Exact10")
    elif scenario == "unrelated_noise":
        (repo / "unrelated-staged.txt").write_text("staged\n")
        _run_git(repo, "add", "--", "unrelated-staged.txt")
        (repo / "unrelated-untracked.txt").write_text("untracked\n")
        cache = repo / ".pytest_cache" / "ignored"
        cache.parent.mkdir()
        cache.write_text("cache\n")
        pycache = repo / "src/covalent_ext/__pycache__/ignored.pyc"
        pycache.parent.mkdir()
        pycache.write_bytes(b"pyc")
    elif scenario == "mixed":
        _run_git(repo, "add", "--", exact_paths[0])
        _run_git(repo, "commit", "-q", "-m", "track one stage path")
    elif scenario == "stage_path_staged":
        _run_git(repo, "add", "--", exact_paths[0])
    elif scenario == "tracked_dirty":
        _run_git(repo, "add", "--", *exact_paths)
        _run_git(repo, "commit", "-q", "-m", "track Exact10")
        (repo / checker.STAGE_PATHS[0]).write_text("dirty\n")
    elif scenario == "missing":
        (repo / checker.STAGE_PATHS[-1]).unlink()
    elif scenario == "ignored":
        exclude = repo / ".git/info/exclude"
        exclude.write_text(exclude.read_text() + exact_paths[0] + "\n")
    elif scenario == "extra_output":
        (repo / checker.OUTPUT_ROOT / "seventh.csv").write_text("extra\n")
    elif scenario == "extra_top_level":
        (repo / "scripts/extra_admit_013_rule_logic_interface_probe.py").write_text(
            "extra\n"
        )
    elif scenario == "nonancestor":
        empty_tree = _run_git(repo, "mktree", input_text="")
        base = _run_git(repo, "commit-tree", empty_tree, "-m", "disconnected")

    monkeypatch.setattr(checker, "REPO_ROOT", repo)
    monkeypatch.setattr(checker, "BASE_COMMIT", base)
    if expected is None:
        with pytest.raises((FileNotFoundError, ValueError)):
            checker._check_lifecycle()
    else:
        assert checker._check_lifecycle() == expected


def test_independent_checker_and_lifecycle_contract():
    checker = _load_checker()
    report = checker.check()
    assert report["all_checks_passed"] is True
    assert report["lifecycle"] in {"pre_commit", "post_commit"}
    assert report["truth_rows"] == 128
    assert report["business_rows"] == 23
    assert report["negative_result_rows"] == 26
