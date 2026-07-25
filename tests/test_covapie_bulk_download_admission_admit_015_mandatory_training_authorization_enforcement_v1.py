from __future__ import annotations

import ast
import copy
import csv
import hashlib
import importlib.util
import inspect
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
    covapie_bulk_download_admission_admit_015_mandatory_training_authorization_enforcement
    as enforcement,
)
from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015
    as exact15_runtime,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_PATH = (
    REPO_ROOT
    / "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_015_mandatory_training_"
    "authorization_enforcement.py"
)
CHECKER_PATH = (
    REPO_ROOT
    / "scripts/"
    "check_covapie_bulk_download_admission_admit_015_mandatory_training_"
    "authorization_enforcement_v1.py"
)
SUMMARY_PATH = (
    REPO_ROOT
    / "docs/"
    "covapie_bulk_download_admission_admit_015_mandatory_training_"
    "authorization_enforcement_v1_summary.md"
)
DERIVED_ROOT = (
    REPO_ROOT
    / "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_015_mandatory_training_"
    "authorization_enforcement_v1"
)
PUBLIC_MARKER = (
    "# === CovaPIE ADMIT_015 MANDATORY TRAINING AUTHORIZATION "
    "ENFORCEMENT PUBLIC CLOSURE END ==="
)
ERROR_FIELDS = (
    "schema_version",
    "error_code",
    "admission_rule_id",
    "reason",
)
RESULT_FIELDS = (
    "schema_version",
    "admission_rule_id",
    "admission_rule_name",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "normalized_values",
    "validated_candidate_fields",
    "consumed_candidate_fields",
    "consumed_context_items",
    "evaluator_io_used",
    "adapter_id",
)
EXACT10 = (
    PRODUCTION_PATH,
    CHECKER_PATH,
    Path(__file__),
    SUMMARY_PATH,
    DERIVED_ROOT
    / "covapie_admit_015_mandatory_training_authorization_"
    "enforcement_implementation_contract.csv",
    DERIVED_ROOT
    / "covapie_admit_015_mandatory_training_authorization_"
    "enforcement_error_and_result_contract.csv",
    DERIVED_ROOT
    / "covapie_admit_015_mandatory_training_authorization_"
    "enforcement_runtime_truth_matrix.csv",
    DERIVED_ROOT
    / "covapie_admit_015_mandatory_training_authorization_"
    "enforcement_protected_action_safety_audit.csv",
    DERIVED_ROOT
    / "covapie_admit_015_mandatory_training_authorization_"
    "enforcement_issue_readiness_inventory.csv",
    DERIVED_ROOT
    / "covapie_admit_015_mandatory_training_authorization_"
    "enforcement_manifest.json",
)


def _load_checker():
    spec = importlib.util.spec_from_file_location(
        "covapie_admit_015_enforcement_revised_checker",
        CHECKER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load_checker()


def _canonical_result():
    return exact15_runtime.UnifiedAdmissionRuleEvaluation(
        schema_version="covapie_unified_admission_rule_evaluation_v1",
        admission_rule_id="ADMIT_015",
        admission_rule_name="current_gate_grants_no_training_permission",
        outcome="passed",
        passed=True,
        blocks_candidate=False,
        reason="",
        normalized_values=(
            ("current_stage_training_authorized", "true"),
        ),
        validated_candidate_fields=(),
        consumed_candidate_fields=(),
        consumed_context_items=("current_stage_training_authorized",),
        evaluator_io_used=False,
        adapter_id="covapie_admit_015_unified_adapter_v1",
    )


def _capture_dispatch(monkeypatch, result):
    calls = []

    def dispatcher(admission_rule_id, candidate_record, **contexts):
        calls.append((admission_rule_id, candidate_record, contexts))
        if isinstance(result, BaseException):
            raise result
        return result

    monkeypatch.setattr(
        exact15_runtime,
        "evaluate_admission_rule",
        dispatcher,
    )
    return calls


def _assert_error(error, code):
    assert type(error) is (
        enforcement.Admit015TrainingAuthorizationEnforcementError
    )
    assert tuple(vars(error)) == ERROR_FIELDS
    assert tuple(field.name for field in fields(type(error))) == ERROR_FIELDS
    assert all(type(value) is str for value in vars(error).values())
    assert error.schema_version == (
        "covapie_admit_015_training_authorization_enforcement_error_v1"
    )
    assert error.error_code == code
    assert error.admission_rule_id == "ADMIT_015"
    assert error.reason == code
    assert "secret-dispatch-message" not in repr(error)
    assert "secret-dispatch-message" not in str(error)


def _mutated_result(field_name, value):
    result = _canonical_result()
    object.__setattr__(result, field_name, value)
    return result


def test_public_signature_is_exact_and_rejects_bypass_keywords(monkeypatch):
    signature = inspect.signature(
        enforcement.require_admit_015_training_authorization
    )
    parameters = tuple(signature.parameters.values())
    assert tuple(parameter.name for parameter in parameters) == (
        "candidate_record",
        "stage_authorization_context",
    )
    assert parameters[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameters[1].kind is inspect.Parameter.KEYWORD_ONLY
    assert str(parameters[0].annotation) == "Mapping[str, object]"
    assert str(parameters[1].annotation) == (
        "Mapping[str, object] | None"
    )
    assert str(signature.return_annotation) == (
        "UnifiedAdmissionRuleEvaluation"
    )

    calls = _capture_dispatch(monkeypatch, _canonical_result())
    for keyword in (
        "precomputed_result",
        "combined_verdict",
        "admit014_permission",
        "dispatcher",
    ):
        with pytest.raises(TypeError):
            enforcement.require_admit_015_training_authorization(
                {},
                stage_authorization_context={},
                **{keyword: object()},
            )
    assert calls == []


def test_error_type_is_exact_frozen_and_rejects_non_exact_strings():
    code = enforcement.ERROR_CODES[0]
    error = enforcement.Admit015TrainingAuthorizationEnforcementError(
        enforcement.ERROR_SCHEMA_VERSION,
        code,
        "ADMIT_015",
        code,
    )
    _assert_error(error, code)
    with pytest.raises(FrozenInstanceError):
        error.reason = "changed"

    class StringSubclass(str):
        pass

    invalid_values = (True, 1, StringSubclass(code))
    for invalid in invalid_values:
        with pytest.raises(TypeError):
            enforcement.Admit015TrainingAuthorizationEnforcementError(
                enforcement.ERROR_SCHEMA_VERSION,
                invalid,
                "ADMIT_015",
                code,
            )


def test_exact6_error_vocabulary_and_reachability_are_frozen():
    assert enforcement.ERROR_CODES == (
        "ADMIT_015_TRAINING_AUTHORIZATION_DISPATCH_FAILED",
        "ADMIT_015_TRAINING_AUTHORIZATION_RESULT_INVALID",
        "ADMIT_015_TRAINING_AUTHORIZATION_DENIED",
        "ADMIT_015_TRAINING_AUTHORIZATION_REPLAY_FORBIDDEN",
        "ADMIT_015_TRAINING_AUTHORIZATION_REPEATED_CALL_FORBIDDEN",
        "ADMIT_015_TRAINING_AUTHORIZATION_OVERRIDE_FORBIDDEN",
    )
    assert enforcement.ERROR_CODES[:3] == (
        "ADMIT_015_TRAINING_AUTHORIZATION_DISPATCH_FAILED",
        "ADMIT_015_TRAINING_AUTHORIZATION_RESULT_INVALID",
        "ADMIT_015_TRAINING_AUTHORIZATION_DENIED",
    )
    assert enforcement.ERROR_CODES[3:] == (
        "ADMIT_015_TRAINING_AUTHORIZATION_REPLAY_FORBIDDEN",
        "ADMIT_015_TRAINING_AUTHORIZATION_REPEATED_CALL_FORBIDDEN",
        "ADMIT_015_TRAINING_AUTHORIZATION_OVERRIDE_FORBIDDEN",
    )


def test_canonical_pass_calls_runtime_once_and_returns_identity(monkeypatch):
    candidate = object()
    stage = object()
    result = _canonical_result()
    calls = _capture_dispatch(monkeypatch, result)

    observed = enforcement.require_admit_015_training_authorization(
        candidate,
        stage_authorization_context=stage,
    )

    assert observed is result
    assert len(calls) == 1
    rule_id, routed_candidate, contexts = calls[0]
    assert rule_id == "ADMIT_015"
    assert routed_candidate is candidate
    assert contexts == {
        "batch_context": None,
        "evaluation_context": None,
        "download_result_context": None,
        "stage_authorization_context": stage,
    }
    assert contexts["stage_authorization_context"] is stage


def test_candidate_and_stage_are_not_read_by_guard(monkeypatch):
    class Unreadable:
        def __getattribute__(self, name):
            raise AssertionError("guard read probe")

        def __iter__(self):
            raise AssertionError("guard iterated probe")

        def __getitem__(self, key):
            raise AssertionError("guard indexed probe")

    candidate = Unreadable()
    stage = Unreadable()
    calls = _capture_dispatch(monkeypatch, _canonical_result())
    enforcement.require_admit_015_training_authorization(
        candidate,
        stage_authorization_context=stage,
    )
    assert calls[0][1] is candidate
    assert calls[0][2]["stage_authorization_context"] is stage


def test_dispatch_failure_is_mapped_without_message_leak(monkeypatch):
    calls = _capture_dispatch(
        monkeypatch,
        RuntimeError("secret-dispatch-message"),
    )
    with pytest.raises(
        enforcement.Admit015TrainingAuthorizationEnforcementError
    ) as raised:
        enforcement.require_admit_015_training_authorization(
            {},
            stage_authorization_context={},
        )
    _assert_error(raised.value, enforcement.ERROR_CODES[0])
    assert len(calls) == 1


@pytest.mark.parametrize("wrong_result", [None, False, object()])
def test_wrong_result_type_is_result_invalid(monkeypatch, wrong_result):
    calls = _capture_dispatch(monkeypatch, wrong_result)
    with pytest.raises(
        enforcement.Admit015TrainingAuthorizationEnforcementError
    ) as raised:
        enforcement.require_admit_015_training_authorization(
            {},
            stage_authorization_context={},
        )
    _assert_error(raised.value, enforcement.ERROR_CODES[1])
    assert len(calls) == 1


def test_result_subclass_is_result_invalid(monkeypatch):
    class ResultSubclass(exact15_runtime.UnifiedAdmissionRuleEvaluation):
        pass

    result = ResultSubclass(*vars(_canonical_result()).values())
    calls = _capture_dispatch(monkeypatch, result)
    with pytest.raises(
        enforcement.Admit015TrainingAuthorizationEnforcementError
    ) as raised:
        enforcement.require_admit_015_training_authorization(
            {},
            stage_authorization_context={},
        )
    _assert_error(raised.value, enforcement.ERROR_CODES[1])
    assert len(calls) == 1


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("schema_version", "schema-drift"),
        ("admission_rule_id", "ADMIT_014"),
        ("admission_rule_name", 1),
        ("outcome", "blocked"),
        ("passed", False),
        ("blocks_candidate", True),
        ("reason", "not-empty"),
        ("normalized_values", ()),
        (
            "normalized_values",
            (("current_stage_training_authorized", "false"),),
        ),
        ("validated_candidate_fields", (("candidate", "value"),)),
        ("consumed_candidate_fields", ("candidate",)),
        ("consumed_context_items", ()),
        ("consumed_context_items", ("wrong",)),
        ("evaluator_io_used", True),
        ("adapter_id", "adapter-drift"),
    ),
)
def test_exact_result_semantic_or_type_drift_is_denied(
    monkeypatch,
    field_name,
    value,
):
    calls = _capture_dispatch(
        monkeypatch,
        _mutated_result(field_name, value),
    )
    with pytest.raises(
        enforcement.Admit015TrainingAuthorizationEnforcementError
    ) as raised:
        enforcement.require_admit_015_training_authorization(
            {},
            stage_authorization_context={},
        )
    _assert_error(raised.value, enforcement.ERROR_CODES[2])
    assert len(calls) == 1


def test_exact13_storage_order_drift_is_denied(monkeypatch):
    result = _canonical_result()
    value = vars(result).pop("schema_version")
    vars(result)["schema_version"] = value
    calls = _capture_dispatch(monkeypatch, result)
    with pytest.raises(
        enforcement.Admit015TrainingAuthorizationEnforcementError
    ) as raised:
        enforcement.require_admit_015_training_authorization(
            {},
            stage_authorization_context={},
        )
    _assert_error(raised.value, enforcement.ERROR_CODES[2])
    assert len(calls) == 1


def test_exact13_dataclass_order_drift_is_denied(monkeypatch):
    result = _canonical_result()
    real_fields = fields(type(result))
    monkeypatch.setattr(
        enforcement,
        "fields",
        lambda result_type: tuple(reversed(real_fields)),
    )
    calls = _capture_dispatch(monkeypatch, result)
    with pytest.raises(
        enforcement.Admit015TrainingAuthorizationEnforcementError
    ) as raised:
        enforcement.require_admit_015_training_authorization(
            {},
            stage_authorization_context={},
        )
    _assert_error(raised.value, enforcement.ERROR_CODES[2])
    assert len(calls) == 1


def test_nested_pair_subclass_is_denied(monkeypatch):
    class TupleSubclass(tuple):
        pass

    result = _mutated_result(
        "normalized_values",
        (
            TupleSubclass(
                ("current_stage_training_authorized", "true")
            ),
        ),
    )
    calls = _capture_dispatch(monkeypatch, result)
    with pytest.raises(
        enforcement.Admit015TrainingAuthorizationEnforcementError
    ) as raised:
        enforcement.require_admit_015_training_authorization(
            {},
            stage_authorization_context={},
        )
    _assert_error(raised.value, enforcement.ERROR_CODES[2])
    assert len(calls) == 1


@pytest.mark.parametrize(
    ("candidate", "stage"),
    (
        ({}, None),
        ({}, {"current_stage_training_authorized": False}),
        (object(), {"current_stage_training_authorized": True}),
    ),
)
def test_real_runtime_nonpass_paths_are_denied(candidate, stage):
    with pytest.raises(
        enforcement.Admit015TrainingAuthorizationEnforcementError
    ) as raised:
        enforcement.require_admit_015_training_authorization(
            candidate,
            stage_authorization_context=stage,
        )
    _assert_error(raised.value, enforcement.ERROR_CODES[2])


def test_real_runtime_canonical_synthetic_pass_does_not_train():
    result = enforcement.require_admit_015_training_authorization(
        {},
        stage_authorization_context={
            "current_stage_training_authorized": True
        },
    )
    assert type(result) is exact15_runtime.UnifiedAdmissionRuleEvaluation
    assert result.passed is True
    assert result.normalized_values == (
        ("current_stage_training_authorized", "true"),
    )
    assert not hasattr(enforcement, "current_permission")
    assert not hasattr(
        enforcement,
        "authorized_admit_015_training_execution_count",
    )


def test_public_function_ast_has_one_dispatch_site_and_no_bypass():
    source = PRODUCTION_PATH.read_text()
    assert source.count(PUBLIC_MARKER) == 1
    public_source = source.split(PUBLIC_MARKER, 1)[0]
    tree = ast.parse(public_source)
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "require_admit_015_training_authorization"
    )
    dispatch_calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "exact15_runtime"
        and node.func.attr == "evaluate_admission_rule"
    ]
    assert len(dispatch_calls) == 1
    assert not any(
        isinstance(node, (ast.For, ast.AsyncFor, ast.While))
        for node in ast.walk(function)
    )
    called_names = {
        node.func.id
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not {"eval", "exec", "__import__"} & called_names
    names = {
        node.id for node in ast.walk(function) if isinstance(node, ast.Name)
    }
    assert function.name not in called_names
    assert not {
        "combined_verdict",
        "admit014_permission",
        "precomputed_result",
        "dispatcher",
    } & names


def test_public_closure_import_and_io_boundary():
    source = PRODUCTION_PATH.read_text()
    public_source = source.split(PUBLIC_MARKER, 1)[0]
    tree = ast.parse(public_source)
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".", 1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            imported_roots.add((node.module or "").split(".", 1)[0])
    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "typing",
        "covalent_ext",
    }
    forbidden = {
        "torch",
        "numpy",
        "pytorch_lightning",
        "rdkit",
        "Bio",
        "gemmi",
        "requests",
        "urllib",
        "pathlib",
        "os",
        "subprocess",
    }
    assert not imported_roots & forbidden
    assert not any(
        isinstance(node, ast.With) for node in ast.walk(tree)
    )


def test_exact10_inventory_and_evidence_contract():
    assert len(EXACT10) == 10
    assert len(set(EXACT10)) == 10
    assert all(path.is_file() for path in EXACT10)
    assert {path.name for path in DERIVED_ROOT.iterdir()} == {
        path.name for path in EXACT10[4:]
    }
    assert hashlib.sha256(PRODUCTION_PATH.read_bytes()).hexdigest() == (
        checker.PRODUCTION_SHA256
    )
    payloads = checker.read_exact6_no_follow()
    assert tuple(payloads) == checker.DERIVED_NAMES
    assert {
        name: hashlib.sha256(content).hexdigest()
        for name, content in payloads.items()
        if name in checker.EXPECTED_DERIVED_SHA256
    } == checker.EXPECTED_DERIVED_SHA256
    assert checker.MANIFEST_NAME not in checker.EXPECTED_DERIVED_SHA256


def test_checker_local_full_csv_and_manifest_reconstruction():
    payloads = checker.read_exact6_no_follow()
    sources = checker.attest_committed_sources()
    support_file_sha256 = checker.read_support_file_sha256()
    observed = checker._verify_semantics(
        payloads,
        sources,
        support_file_sha256,
    )
    checker._assert_recursive_exact(
        observed,
        checker._expected_manifest(support_file_sha256),
    )
    expected_sets = (
        (
            checker.IMPLEMENTATION_NAME,
            checker.IMPLEMENTATION_COLUMNS,
            checker._expected_implementation_rows(),
            38,
        ),
        (
            checker.ERROR_RESULT_NAME,
            checker.ERROR_RESULT_COLUMNS,
            checker._expected_error_result_rows(),
            33,
        ),
        (
            checker.TRUTH_NAME,
            checker.TRUTH_COLUMNS,
            checker._expected_truth_rows(),
            23,
        ),
        (
            checker.PROTECTED_NAME,
            checker.PROTECTED_COLUMNS,
            checker._expected_protected_rows(),
            11,
        ),
    )
    for name, columns, expected, count in expected_sets:
        actual = checker._csv_rows(payloads[name], columns)
        assert len(actual) == count
        checker._assert_recursive_exact(actual, expected)


def test_source_attestation_is_exact_stage0_blob_and_filesystem_identity():
    records = checker.attest_committed_sources()
    assert len(records) == 5
    assert tuple(record.relative_path for record in records) == tuple(
        row[0] for row in checker.SOURCE_BOUNDARY
    )
    for record, frozen in zip(
        records,
        checker.SOURCE_BOUNDARY,
        strict=True,
    ):
        relative, digest, mode, blob = frozen
        assert record.relative_path == relative
        assert record.sha256 == digest
        assert record.base_mode == record.index_mode == mode == "100644"
        assert record.base_blob == record.index_blob == blob
        assert record.index_stage == 0
        assert hashlib.sha256(record.content).hexdigest() == digest


def _verification_inputs():
    return (
        checker.read_exact6_no_follow(),
        checker.attest_committed_sources(),
        checker.read_support_file_sha256(),
    )


def _serialize_manifest(value):
    return (
        json.dumps(value, indent=2, ensure_ascii=True) + "\n"
    ).encode()


def _legacy_support_sha256():
    return {
        checker.CHECKER_REL.as_posix(): (
            "ecb08e79675abf809e6c39435980cae6"
            + "5b8e50ad8477d4d7e440eaf8cc8a8ed8"
        ),
        checker.TESTS_REL.as_posix(): (
            "51a7c84526e2d31ab9f019d30a145ce2"
            + "6c8401b6e038f2d78a60be88aacf08c9"
        ),
        checker.SUMMARY_REL.as_posix(): (
            "e4ccec5e5f32f5de9ed41c0c4fda333"
            + "c7216abd004113355969db6e1a42f89d9"
        ),
    }


def test_manifest_output_sha256_matches_current_exact9_bytes():
    payloads = checker.read_exact6_no_follow()
    manifest = checker._strict_json(payloads[checker.MANIFEST_NAME])
    support_file_sha256 = checker.read_support_file_sha256()
    expected_manifest = checker._expected_manifest(support_file_sha256)
    expected_output = expected_manifest["output_sha256"]
    actual_output = {
        relative: hashlib.sha256(
            checker._read_repo_relative_no_follow(
                REPO_ROOT,
                Path(relative),
            )
        ).hexdigest()
        for relative in manifest["output_sha256"]
    }
    assert len(actual_output) == 9
    assert tuple(manifest["output_sha256"]) == tuple(expected_output)
    assert manifest["output_sha256"] == actual_output == expected_output
    assert manifest["output_sha256_excludes_manifest_self_hash"] is True


def test_legacy_support_hashes_and_manifest_hash_constant_are_absent():
    paths = (
        checker.CHECKER_REL,
        checker.TESTS_REL,
        checker.SUMMARY_REL,
        checker.STAGE / checker.MANIFEST_NAME,
    )
    contents = tuple(
        checker._read_repo_relative_no_follow(REPO_ROOT, relative)
        for relative in paths
    )
    for legacy_digest in _legacy_support_sha256().values():
        assert all(legacy_digest.encode("ascii") not in content for content in contents)
    assert b"MANIFEST_" + b"SHA256" not in contents[0]


def test_dynamic_support_hashes_are_integrity_only_not_business_authority():
    support_file_sha256 = checker.read_support_file_sha256()
    drifted_support = dict(support_file_sha256)
    drifted_support[checker.CHECKER_REL.as_posix()] = "0" * 64
    expected = checker._expected_manifest(support_file_sha256)
    drifted = checker._expected_manifest(drifted_support)
    expected_output = expected.pop("output_sha256")
    drifted_output = drifted.pop("output_sha256")
    checker._assert_recursive_exact(expected, drifted)
    assert tuple(expected_output) == tuple(drifted_output)
    assert {
        path
        for path in expected_output
        if expected_output[path] != drifted_output[path]
    } == {checker.CHECKER_REL.as_posix()}
    assert expected["production_contract"]["public_function_name"] == (
        "require_admit_015_training_authorization"
    )
    assert expected["error_contract"]["error_codes"] == list(
        checker.ERROR_CODES
    )
    assert expected["pass_invariants"]["field_order"] == list(
        checker.RESULT_FIELDS
    )
    assert expected["precondition_transition"][
        "remaining_open_precondition_ids"
    ] == ["PRE_035", "PRE_036", "PRE_038", "PRE_042"]
    assert expected["canonical_masks"][3] == {
        "alias": "B3",
        "semantic_name": "scaffold_only",
    }
    assert expected["readiness"]["ready_for_training"] is False
    assert expected["scope"]["real_training"] is False
    assert expected["recommended_next_step"] == (
        "design_covapie_combined_permission_semantics_contract_v1"
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "legacy_three",
        "checker_sha",
        "tests_sha",
        "summary_sha",
        "support_path_missing",
        "support_path_extra",
        "output_path_reorder",
    ),
)
def test_manifest_support_file_hash_contract_fails_closed(mutation):
    payloads, sources, support_file_sha256 = _verification_inputs()
    manifest = checker._strict_json(payloads[checker.MANIFEST_NAME])
    output_sha256 = manifest["output_sha256"]
    if mutation == "legacy_three":
        output_sha256.update(_legacy_support_sha256())
    elif mutation in {"checker_sha", "tests_sha", "summary_sha"}:
        relative = {
            "checker_sha": checker.CHECKER_REL,
            "tests_sha": checker.TESTS_REL,
            "summary_sha": checker.SUMMARY_REL,
        }[mutation]
        output_sha256[relative.as_posix()] = "0" * 64
    elif mutation == "support_path_missing":
        del output_sha256[checker.SUMMARY_REL.as_posix()]
    elif mutation == "support_path_extra":
        output_sha256["docs/unexpected_support_file.md"] = "0" * 64
    else:
        manifest["output_sha256"] = {
            key: output_sha256[key] for key in reversed(tuple(output_sha256))
        }
    payloads[checker.MANIFEST_NAME] = _serialize_manifest(manifest)
    with pytest.raises(ValueError):
        checker._verify_semantics(
            payloads,
            sources,
            support_file_sha256,
        )


def _synchronize_manifest_output_sha(
    payloads,
    manifest,
    name,
):
    relative = f"{checker.STAGE.as_posix()}/{name}"
    manifest["output_sha256"][relative] = hashlib.sha256(
        payloads[name]
    ).hexdigest()
    payloads[checker.MANIFEST_NAME] = _serialize_manifest(manifest)


@pytest.mark.parametrize(
    "mutation",
    (
        "implementation_row",
        "error_code",
        "error_reachability",
        "truth_case_id",
        "truth_observed_decision",
        "protected_semantic",
        "protected_count",
        "issue_row",
    ),
)
def test_synchronized_csv_and_manifest_sha_tamper_fails_closed(mutation):
    payloads, sources, support_file_sha256 = _verification_inputs()
    manifest = checker._strict_json(payloads[checker.MANIFEST_NAME])
    if mutation == "implementation_row":
        name = checker.IMPLEMENTATION_NAME
        columns = checker.IMPLEMENTATION_COLUMNS
        rows = checker._csv_rows(payloads[name], columns)
        rows[0]["contract_item"] = "candidate_public_function"
    elif mutation in {"error_code", "error_reachability"}:
        name = checker.ERROR_RESULT_NAME
        columns = checker.ERROR_RESULT_COLUMNS
        rows = checker._csv_rows(payloads[name], columns)
        target = 27 if mutation == "error_code" else 30
        field = "error_code" if mutation == "error_code" else "reachability"
        rows[target][field] = "synchronized_drift"
    elif mutation in {"truth_case_id", "truth_observed_decision"}:
        name = checker.TRUTH_NAME
        columns = checker.TRUTH_COLUMNS
        rows = checker._csv_rows(payloads[name], columns)
        field = (
            "case_id"
            if mutation == "truth_case_id"
            else "observed_decision"
        )
        rows[0][field] = "synchronized_drift"
    elif mutation in {"protected_semantic", "protected_count"}:
        name = checker.PROTECTED_NAME
        columns = checker.PROTECTED_COLUMNS
        rows = checker._csv_rows(payloads[name], columns)
        field = (
            "action_semantic_name"
            if mutation == "protected_semantic"
            else "implementation_call_count"
        )
        rows[0][field] = "synchronized_drift"
    else:
        name = checker.ISSUES_NAME
        columns = checker.ISSUE_COLUMNS
        rows = checker._csv_rows(payloads[name], columns)
        rows[0]["issue_id"] = "synchronized_drift"
    payloads[name] = checker._csv_bytes(columns, rows)
    _synchronize_manifest_output_sha(payloads, manifest, name)
    with pytest.raises(ValueError):
        checker._verify_semantics(
            payloads,
            sources,
            support_file_sha256,
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "public_signature",
        "manifest_error_code",
        "exact13_invariant",
        "remove_b3",
        "readiness_bool_to_int",
        "pre_open_ids",
        "source_sha",
        "exact10_order",
        "scope",
        "recommended_next_step",
        "nested_missing",
        "nested_extra",
        "nested_reorder",
    ),
)
def test_complete_manifest_tamper_fails_closed(mutation):
    payloads, sources, support_file_sha256 = _verification_inputs()
    manifest = checker._strict_json(payloads[checker.MANIFEST_NAME])
    if mutation == "public_signature":
        manifest["production_contract"]["exact_signature"] = "drift"
    elif mutation == "manifest_error_code":
        manifest["error_contract"]["error_codes"][0] = "drift"
    elif mutation == "exact13_invariant":
        manifest["pass_invariants"]["outcome"] = "blocked"
    elif mutation == "remove_b3":
        del manifest["canonical_masks"][3]
    elif mutation == "readiness_bool_to_int":
        manifest["readiness"][
            "mandatory_training_authorization_enforcement_implemented"
        ] = 1
    elif mutation == "pre_open_ids":
        manifest["precondition_transition"][
            "remaining_open_precondition_ids"
        ] = ["PRE_035"]
    elif mutation == "source_sha":
        first = next(iter(manifest["source_boundary_sha256"]))
        manifest["source_boundary_sha256"][first] = "0" * 64
    elif mutation == "exact10_order":
        manifest["exact10_files"][0:2] = reversed(
            manifest["exact10_files"][0:2]
        )
    elif mutation == "scope":
        manifest["scope"]["combined_permission_semantics"] = True
    elif mutation == "recommended_next_step":
        manifest["recommended_next_step"] = "drift"
    elif mutation == "nested_missing":
        del manifest["readiness"]["ready_for_training"]
    elif mutation == "nested_extra":
        manifest["readiness"]["extra"] = False
    elif mutation == "nested_reorder":
        readiness = manifest["readiness"]
        keys = tuple(readiness)
        manifest["readiness"] = {
            key: readiness[key] for key in reversed(keys)
        }
    payloads[checker.MANIFEST_NAME] = _serialize_manifest(manifest)
    with pytest.raises(ValueError):
        checker._verify_semantics(
            payloads,
            sources,
            support_file_sha256,
        )


@pytest.mark.parametrize(
    "mutation",
    ("public_function", "public_signature", "error_code", "exact13"),
)
def test_production_or_runtime_synchronized_business_tamper_rejected(
    monkeypatch,
    mutation,
):
    production = PRODUCTION_PATH.read_bytes()
    if mutation == "public_function":
        tampered = production.replace(
            b"require_admit_015_training_authorization",
            b"require_admit_015_training_authorization_drift",
            1,
        )
        with pytest.raises(ValueError):
            checker._check_signature_and_ast(tampered)
    elif mutation == "public_signature":
        tampered = production.replace(
            b"stage_authorization_context: Mapping[str, object] | None",
            b"stage_authorization_context: object",
            1,
        )
        with pytest.raises(ValueError):
            checker._check_signature_and_ast(tampered)
    elif mutation == "error_code":
        monkeypatch.setattr(
            enforcement,
            "ERROR_CODES",
            ("synchronized_drift", *enforcement.ERROR_CODES[1:]),
        )
        with pytest.raises(ValueError):
            checker._check_error_type()
    else:
        tampered = production.replace(
            b'result.outcome != "passed"',
            b'result.outcome != "blocked"',
            1,
        )
        with pytest.raises(ValueError):
            checker._check_signature_and_ast(tampered)


def _copy_exact6(tmp_path):
    parent = tmp_path / "derived"
    root = parent / checker.STAGE.name
    root.mkdir(parents=True)
    for name in checker.DERIVED_NAMES:
        shutil.copy2(checker.DERIVED_ROOT / name, root / name)
    return root


def test_hardened_exact6_normal_reader():
    payloads = checker.read_exact6_no_follow()
    assert tuple(payloads) == checker.DERIVED_NAMES


def test_hardened_exact6_rejects_seventh_file(tmp_path):
    root = _copy_exact6(tmp_path)
    (root / "seventh.txt").write_text("extra")
    with pytest.raises(ValueError):
        checker.read_exact6_no_follow(root)


def test_hardened_exact6_rejects_missing_leaf(tmp_path):
    root = _copy_exact6(tmp_path)
    (root / checker.IMPLEMENTATION_NAME).unlink()
    with pytest.raises(ValueError):
        checker.read_exact6_no_follow(root)


def test_hardened_exact6_rejects_symlink_without_reading_target(tmp_path):
    root = _copy_exact6(tmp_path)
    target = tmp_path / "external-secret"
    target.write_text("must-not-be-opened")
    before = (target.stat().st_ino, target.read_bytes())
    leaf = root / checker.IMPLEMENTATION_NAME
    leaf.unlink()
    leaf.symlink_to(target)
    with pytest.raises((OSError, ValueError)):
        checker.read_exact6_no_follow(root)
    assert (target.stat().st_ino, target.read_bytes()) == before


def test_hardened_exact6_rejects_same_byte_leaf_replacement(tmp_path):
    root = _copy_exact6(tmp_path)
    replaced = False

    def hook(event, observed_root):
        nonlocal replaced
        if event == "after_leaf_open" and not replaced:
            leaf = observed_root / checker.IMPLEMENTATION_NAME
            replacement = observed_root / "replacement"
            replacement.write_bytes(leaf.read_bytes())
            os.replace(replacement, leaf)
            replaced = True

    with pytest.raises(ValueError):
        checker.read_exact6_no_follow(root, hook=hook)


def test_hardened_exact6_rejects_root_replacement(tmp_path):
    root = _copy_exact6(tmp_path)
    replaced = False

    def hook(event, observed_root):
        nonlocal replaced
        if event == "after_root_open" and not replaced:
            old = observed_root.with_name(observed_root.name + "-old")
            os.rename(observed_root, old)
            shutil.copytree(old, observed_root)
            replaced = True

    with pytest.raises(ValueError):
        checker.read_exact6_no_follow(root, hook=hook)


def test_hardened_exact6_rejects_parent_replacement(tmp_path):
    root = _copy_exact6(tmp_path)
    replaced = False

    def hook(event, observed_root):
        nonlocal replaced
        if event == "after_root_open" and not replaced:
            parent = observed_root.parent
            old = parent.with_name(parent.name + "-old")
            os.rename(parent, old)
            parent.mkdir()
            shutil.copytree(old / observed_root.name, parent / observed_root.name)
            replaced = True

    with pytest.raises(ValueError):
        checker.read_exact6_no_follow(root, hook=hook)


def _git(repo, *arguments):
    return subprocess.run(
        ("git", *arguments),
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout


def _commit(repo, message, *, allow_empty=False):
    arguments = [
        "-c",
        "user.name=CovaPIE Test",
        "-c",
        "user.email=covapie-test@example.invalid",
        "commit",
        "-q",
        "-m",
        message,
    ]
    if allow_empty:
        arguments.insert(5, "--allow-empty")
    _git(repo, *arguments)
    return _git(repo, "rev-parse", "HEAD").decode().strip()


def _make_candidate_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    for relative in (
        Path("src/covalent_ext"),
        Path("scripts"),
        Path("tests"),
        Path("docs"),
        Path("data/derived/covalent_small"),
    ):
        (repo / relative).mkdir(parents=True, exist_ok=True)
    (repo / "README").write_text("baseline\n")
    (repo / ".gitignore").write_text("*.ignored\n")
    _git(repo, "add", "--", "README", ".gitignore")
    base = _commit(repo, "baseline")
    for relative in checker.EXACT10:
        destination = repo / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, destination)
        destination.chmod(0o644)
    return repo, base


def test_lifecycle_normal_pre_commit(tmp_path):
    repo, base = _make_candidate_repo(tmp_path)
    assert checker.verify_lifecycle(repo, base=base) == "pre_commit"


def test_lifecycle_normal_post_commit(tmp_path):
    repo, base = _make_candidate_repo(tmp_path)
    _git(repo, "add", "--", *(path.as_posix() for path in checker.EXACT10))
    _commit(repo, "candidate")
    assert checker.verify_lifecycle(repo, base=base) == "post_commit"


def test_lifecycle_descendant_base_pre_commit(tmp_path):
    repo, base = _make_candidate_repo(tmp_path)
    (repo / "baseline-descendant").write_text("noncandidate\n")
    _git(repo, "add", "--", "baseline-descendant")
    _commit(repo, "descendant baseline")
    assert checker.verify_lifecycle(repo, base=base) == "pre_commit"


def test_lifecycle_rejects_allow_empty_head_drift(tmp_path):
    repo, base = _make_candidate_repo(tmp_path)
    _git(repo, "add", "--", *(path.as_posix() for path in checker.EXACT10))
    _commit(repo, "candidate")
    _commit(repo, "empty drift", allow_empty=True)
    with pytest.raises(ValueError):
        checker.verify_lifecycle(repo, base=base)


@pytest.mark.parametrize(
    "bounded_root",
    ("src/covalent_ext", "scripts", "tests", "docs"),
)
def test_lifecycle_rejects_tracked_nested_stage_file(
    tmp_path,
    bounded_root,
):
    repo, _ = _make_candidate_repo(tmp_path)
    residue = (
        repo
        / bounded_root
        / f"{checker.STAGE_TOKEN}_residue"
        / "nested.txt"
    )
    residue.parent.mkdir()
    residue.write_text("tracked residue")
    _git(repo, "add", "--", residue.relative_to(repo).as_posix())
    _commit(repo, "tracked residue")
    with pytest.raises(ValueError):
        checker.assert_exact10_recursive_inventory(repo)


def test_lifecycle_rejects_ignored_nested_stage_file(tmp_path):
    repo, _ = _make_candidate_repo(tmp_path)
    residue = repo / "docs" / f"{checker.STAGE_TOKEN}.ignored"
    residue.write_text("ignored residue")
    with pytest.raises(ValueError):
        checker.assert_exact10_recursive_inventory(repo)


@pytest.mark.parametrize("ignored", (False, True))
def test_lifecycle_rejects_generic_symlink_without_target_access(
    tmp_path,
    ignored,
):
    repo, _ = _make_candidate_repo(tmp_path)
    target = tmp_path / "external"
    target.write_text("external")
    before = (target.stat().st_ino, target.read_bytes())
    name = "generic.ignored" if ignored else "generic-link"
    link = repo / "docs" / name
    link.symlink_to(target)
    if not ignored:
        _git(repo, "add", "--", link.relative_to(repo).as_posix())
        _commit(repo, "tracked generic symlink")
    with pytest.raises(ValueError):
        checker.assert_exact10_recursive_inventory(repo)
    assert (target.stat().st_ino, target.read_bytes()) == before


def test_lifecycle_rejects_matching_derived_sibling(tmp_path):
    repo, _ = _make_candidate_repo(tmp_path)
    sibling = repo / checker.STAGE.parent / (checker.STAGE.name + "_sibling")
    shutil.copytree(repo / checker.STAGE, sibling)
    with pytest.raises(ValueError):
        checker.assert_exact10_recursive_inventory(repo)


@pytest.mark.parametrize("event", ("before_top_root_open", "after_top_root_open"))
def test_lifecycle_rejects_top_root_replacement(tmp_path, event):
    repo, _ = _make_candidate_repo(tmp_path)
    replaced = False

    def hook(observed_event, name):
        nonlocal replaced
        if observed_event == event and name.name == "docs" and not replaced:
            docs = repo / "docs"
            old = repo / "docs-old"
            os.rename(docs, old)
            docs.mkdir()
            replaced = True

    with pytest.raises(ValueError):
        checker.assert_exact10_recursive_inventory(repo, hook=hook)


def test_current_checker_reports_expected_lifecycle_and_empty_stderr():
    tracked = subprocess.run(
        ("git", "ls-files", "--", *(str(path) for path in checker.EXACT10)),
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    assert tracked.stderr == b""
    tracked_exact10 = tuple(line for line in tracked.stdout.splitlines() if line)
    expected_lifecycle = "post_commit" if len(tracked_exact10) == 10 else "pre_commit"

    result = subprocess.run(
        (sys.executable, str(CHECKER_PATH)),
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0
    assert result.stderr == b""
    report = json.loads(result.stdout)
    assert report["lifecycle"] == expected_lifecycle
    assert report["all_checks_passed"] is True
