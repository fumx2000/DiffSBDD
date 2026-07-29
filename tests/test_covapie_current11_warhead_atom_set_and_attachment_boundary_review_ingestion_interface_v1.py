from __future__ import annotations

import ast
import copy
import csv
import hashlib
import inspect
import io
import json
import os
import shutil
import stat
import subprocess
import sys
from dataclasses import fields, is_dataclass, replace
from pathlib import Path
from typing import get_type_hints

import pytest
import rdkit

from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as iface,
)
from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle


ROOT = Path(__file__).resolve().parents[1]
PYTEST_VERSION = "9.1.0"
RDKIT_VERSION = "2022.03.2"
FORBIDDEN_SUFFIXES = {
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".tmp", ".part",
}


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


@pytest.fixture(scope="module")
def build_result():
    result = iface.build_result(ROOT)
    assert result.transaction_succeeded and not result.blocking_reasons
    return result


@pytest.fixture(scope="module")
def truth_cases(build_result):
    assert build_result.design_evidence is not None
    return iface._build_synthetic_truth_cases(build_result.design_evidence)


def _case(truth_cases, name):
    return next(case for case in truth_cases if case.name == name)


def _evaluate(case):
    return iface.evaluate_current11_warhead_boundary_review_ingestion_v1(
        submissions=case.submissions,
        authority_context=case.authority_context,
        existing_authorities=case.existing_authorities,
    )


def _rehash_response(response):
    response["interface_response_sha256"] = iface.interface_response_sha256(
        response
    )


def _validate(response, case):
    return iface.validate_current11_warhead_boundary_review_ingestion_interface_response_v1(
        response,
        submissions=case.submissions,
        authority_context=case.authority_context,
        existing_authorities=case.existing_authorities,
    )


def test_formal_python_pytest_rdkit_environment():
    assert sys.implementation.name == "cpython"
    assert sys.version_info[:3] == (3, 10, 4)
    assert pytest.__version__ == PYTEST_VERSION
    assert rdkit.__version__ == RDKIT_VERSION


def test_base_identity_and_actual_lifecycle():
    identity = subprocess.run(
        (
            "git", "show", "-s", "--format=%H%n%P%n%T%n%s",
            iface.BASE_COMMIT,
        ),
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.decode().splitlines()
    assert identity == [
        iface.BASE_COMMIT,
        iface.BASE_PARENT,
        iface.BASE_TREE,
        iface.BASE_SUBJECT,
    ]
    assert iface.validate_execution_boundary_v1(ROOT) in lifecycle.LIFECYCLES


def test_exact6_sources_exist_only_at_base_and_match_sha():
    payloads = iface.load_frozen_sources(ROOT)
    assert tuple(payloads) == iface.SOURCE_PATHS
    assert len(payloads) == 6
    for path, expected in iface.FROZEN_BASE_SHA256.items():
        assert hashlib.sha256(payloads[path]).hexdigest() == expected
        assert subprocess.run(
            (
                "git", "cat-file", "-e",
                f"{iface.BASE_COMMIT}:{path.as_posix()}",
            ),
            cwd=ROOT,
            check=False,
        ).returncode == 0


def test_design_manifest_state_schema_counts_and_downstream_closed():
    manifest = json.loads(
        iface.base_bytes(ROOT, iface.DESIGN_MANIFEST)
    )
    assert manifest["transaction_succeeded"] is True
    assert manifest[
        "ready_for_review_ingestion_interface_implementation"
    ] is True
    assert manifest["ready_for_review_ingestion_execution"] is False
    assert manifest["completed_review_record_count"] == 0
    assert manifest["ingestion_envelope_count"] == 0
    assert manifest["ingestion_result_count"] == 0
    assert manifest["authority_record_count"] == 0
    assert manifest["completed_review_package_identity_field_count"] == 14
    assert manifest["ingestion_result_field_count"] == 18
    assert manifest["authority_record_field_count"] == 27
    assert manifest["ingestion_result_reason_code_count"] == 31
    assert len(manifest["ingestion_failure_reason_precedence"]) == 10
    assert manifest["failure_mutation_count"] == 51
    assert manifest["canonical_masks"] == list(iface.CANONICAL_MASKS)
    assert manifest["ready_for_training"] is False


def test_public_function_signatures_and_forbidden_keywords():
    builder = inspect.signature(
        iface.build_current11_warhead_boundary_review_ingestion_authority_context_v1
    )
    assert tuple(builder.parameters) == ("repo_root",)
    assert (
        builder.parameters["repo_root"].kind
        is inspect.Parameter.POSITIONAL_OR_KEYWORD
    )
    builder_hints = get_type_hints(
        iface.build_current11_warhead_boundary_review_ingestion_authority_context_v1
    )
    assert builder_hints["repo_root"] is Path
    assert builder_hints["return"] is iface.design.IngestionAuthorityContext

    evaluator = inspect.signature(
        iface.evaluate_current11_warhead_boundary_review_ingestion_v1
    )
    assert tuple(evaluator.parameters) == (
        "submissions", "authority_context", "existing_authorities",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in evaluator.parameters.values()
    )
    assert evaluator.parameters["existing_authorities"].default == ()
    forbidden = {
        "repo_root", "file_path", "csv_path", "json_path", "raw_payload",
        "package_identity_by_sample", "options", "proposals_by_sample",
        "parent_atom_ids_by_ligand", "parent_bonds_by_ligand",
        "valid_sample_ids",
    }
    assert not forbidden & set(evaluator.parameters)


def test_context_builder_does_not_call_design_lifecycle_bound_builder(
    monkeypatch,
):
    def forbidden(*args, **kwargs):
        raise AssertionError("design lifecycle-bound builder was called")

    monkeypatch.setattr(
        iface.design, "build_ingestion_authority_context", forbidden,
    )
    context = (
        iface.build_current11_warhead_boundary_review_ingestion_authority_context_v1(
            ROOT
        )
    )
    iface.design.validate_ingestion_authority_context(context)
    production_source = inspect.getsource(iface)
    assert "design.build_ingestion_authority_context(" not in production_source


def test_public_builder_is_separate_from_strict_artifact_lifecycle(
    monkeypatch,
):
    def strict_artifact_only(*args, **kwargs):
        raise RuntimeError("strict artifact lifecycle sentinel")

    monkeypatch.setattr(
        iface, "validate_execution_boundary_v1", strict_artifact_only,
    )
    context = (
        iface.build_current11_warhead_boundary_review_ingestion_authority_context_v1(
            ROOT
        )
    )
    iface.design.validate_ingestion_authority_context(context)
    with pytest.raises(RuntimeError, match="strict artifact lifecycle sentinel"):
        iface.build_result(ROOT)


def test_public_runtime_repository_and_imported_design_source_integrity():
    assert iface.PUBLIC_RUNTIME_COMPATIBILITY_SCOPE == (
        "interface_base_and_all_descendants_with_frozen_design_source_v1"
    )
    assert iface.PUBLIC_RUNTIME_REQUIRED_BASE_COMMIT == iface.BASE_COMMIT
    assert iface.IMPORTED_DESIGN_SOURCE_SHA256 == (
        "cd726f7122edd8315079f0ac1df9d4bb24d4ee969f438ce2f41eda3fd0f7c410"
    )
    iface._validate_public_runtime_repository_v1(ROOT)
    iface._validate_imported_design_source_integrity_v1(ROOT)
    source = ROOT / iface.DESIGN_PRODUCTION
    info = source.lstat()
    assert stat.S_ISREG(info.st_mode)
    assert not source.is_symlink()
    worktree_payload = source.read_bytes()
    head_payload = subprocess.run(
        (
            "git", "show",
            f"HEAD:{iface.DESIGN_PRODUCTION.as_posix()}",
        ),
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout
    assert worktree_payload == head_payload
    assert hashlib.sha256(worktree_payload).hexdigest() == (
        iface.IMPORTED_DESIGN_SOURCE_SHA256
    )


def test_evaluator_runtime_root_is_inferred_from_interface_module(
    monkeypatch, tmp_path,
):
    monkeypatch.chdir(tmp_path)
    inferred = iface._infer_interface_runtime_repository_root_v1()
    assert inferred == ROOT.resolve()
    assert iface._validate_public_evaluator_runtime_integrity_v1() == inferred
    source = Path(iface.__file__)
    info = source.lstat()
    assert stat.S_ISREG(info.st_mode)
    assert not source.is_symlink()
    assert source.resolve() == (inferred / iface.PRODUCTION_PATH).resolve()


def test_evaluator_first_effective_operation_is_runtime_integrity():
    function = ast.parse(
        inspect.getsource(
            iface.evaluate_current11_warhead_boundary_review_ingestion_v1
        )
    ).body[0]
    assert isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef))
    assert isinstance(function.body[0], ast.Expr)
    assert isinstance(function.body[0].value, ast.Constant)
    first_effective = function.body[1]
    assert isinstance(first_effective, ast.Expr)
    assert isinstance(first_effective.value, ast.Call)
    assert isinstance(first_effective.value.func, ast.Name)
    assert first_effective.value.func.id == (
        "_validate_public_evaluator_runtime_integrity_v1"
    )


def test_public_runtime_invalid_root_and_missing_design_base_fail_closed(
    monkeypatch,
):
    with pytest.raises(
        ValueError, match="^INTERFACE_PUBLIC_RUNTIME_REPOSITORY_INVALID$",
    ):
        iface.build_current11_warhead_boundary_review_ingestion_authority_context_v1(
            ROOT / "src"
        )

    original = iface._git

    def missing_design_base(repo_root, *arguments, **kwargs):
        if arguments == (
            "cat-file", "-e", f"{iface.design.BASE_COMMIT}^{{commit}}",
        ):
            return subprocess.CompletedProcess(
                ("git", *arguments), 1, b"", b"missing object",
            )
        return original(repo_root, *arguments, **kwargs)

    monkeypatch.setattr(iface, "_git", missing_design_base)
    with pytest.raises(
        ValueError, match="^INTERFACE_PUBLIC_RUNTIME_REPOSITORY_INVALID$",
    ):
        iface.build_current11_warhead_boundary_review_ingestion_authority_context_v1(
            ROOT
        )


def test_build_result_does_not_call_design_lifecycle_bound_build_result(
    monkeypatch,
):
    def forbidden(*args, **kwargs):
        raise AssertionError("design lifecycle-bound build_result was called")

    monkeypatch.setattr(iface.design, "build_result", forbidden)
    result = iface.build_result(ROOT)
    assert result.transaction_succeeded
    assert result.design_evidence is not None
    assert not result.blocking_reasons
    production_source = inspect.getsource(iface)
    assert "design.build_result(" not in production_source


def test_context_builder_deterministic_no_working_tree_data_read(monkeypatch):
    observed = []
    original = iface._git

    def recording(repo_root, *arguments, **kwargs):
        observed.append(arguments)
        return original(repo_root, *arguments, **kwargs)

    monkeypatch.setattr(iface, "_git", recording)
    first = (
        iface.build_current11_warhead_boundary_review_ingestion_authority_context_v1(
            ROOT
        )
    )
    second = (
        iface.build_current11_warhead_boundary_review_ingestion_authority_context_v1(
            ROOT
        )
    )
    assert first == second
    assert first is not second
    design_object_reads = [
        arguments[1]
        for arguments in observed
        if len(arguments) == 2
        and arguments[0] == "show"
        and arguments[1].startswith(iface.design.BASE_COMMIT + ":")
    ]
    expected = [
        f"{iface.design.BASE_COMMIT}:{path.as_posix()}"
        for path in iface.design.SOURCE_PATHS
    ]
    assert design_object_reads == expected * 2
    source = inspect.getsource(
        iface._build_committed_design_authority_context_v1
    )
    assert "read_" not in source and "open(" not in source


@pytest.mark.parametrize(
    "name",
    (
        "valid_select",
        "valid_revise",
        "valid_quarantine",
        "valid_partial_two_sample_batch",
        "not_reviewed_blocked",
        "conflicting_reingestion_blocked",
        "atomicity_rollback_blocked",
        "mixed_batch_ids_invalid",
        "duplicate_sample_invalid",
        "duplicate_review_sha_invalid",
        "forged_review_identity_invalid",
        "ineligible_select_invalid",
        "invalid_envelope_exact_type",
        "invalid_existing_authority_hash",
        "invalid_existing_authority_decision_evidence",
        "empty_batch_invalid",
        "oversized_batch_invalid",
    ),
)
def test_exact18_evaluator_cases_except_rejected_context(truth_cases, name):
    case = _case(truth_cases, name)
    response = _evaluate(case)
    observed_outcome = (
        "passed"
        if response["batch_passed"]
        else "blocked"
        if any(
            row["outcome"] == "blocked"
            for row in response["ingestion_result_records"]
        )
        else "invalid"
    )
    assert response["batch_passed"] is case.expected_batch_passed
    assert observed_outcome == case.expected_outcome_class
    assert tuple(
        row["reason"] for row in response["ingestion_result_records"]
    ) == case.expected_reasons
    assert len(response["ingestion_result_records"]) == len(case.submissions)
    assert (
        len(response["new_authority_records"])
        == case.expected_new_authority_count
    )


def test_forged_context_fails_closed_at_response_boundary(truth_cases):
    case = _case(truth_cases, "forged_authority_context_invalid")
    batch = iface.design.ingest_review_batch(
        case.submissions,
        authority_context=case.authority_context,
    )
    assert batch.passed is False
    assert [row["reason"] for row in batch.result_records] == [
        "INGESTION_AUTHORITY_CONTEXT_INVALID"
    ]
    with pytest.raises(ValueError, match="INGESTION_AUTHORITY_CONTEXT_INVALID"):
        _evaluate(case)


def test_exact6_schema_types_hash_and_no_nondeterministic_tokens(truth_cases):
    response = _evaluate(_case(truth_cases, "valid_partial_two_sample_batch"))
    assert tuple(response) == iface.INTERFACE_RESPONSE_FIELDS
    assert type(response) is dict
    assert type(response["interface_response_version"]) is str
    assert type(response["authority_context_record_sha256"]) is str
    assert type(response["batch_passed"]) is bool
    assert type(response["ingestion_result_records"]) is tuple
    assert type(response["new_authority_records"]) is tuple
    assert type(response["interface_response_sha256"]) is str
    assert iface._SHA.fullmatch(response["interface_response_sha256"])
    assert (
        response["interface_response_sha256"]
        == iface.interface_response_sha256(response)
    )
    payload = iface.canonical_json(iface._response_hash_payload(response))
    assert "interface_response_sha256" not in payload
    assert "timestamp" not in payload.lower()
    assert "uuid" not in payload.lower()
    assert str(ROOT) not in payload
    assert "0x" not in payload


def test_response_records_retain_exact18_and_exact27(truth_cases):
    response = _evaluate(_case(truth_cases, "valid_partial_two_sample_batch"))
    for record in response["ingestion_result_records"]:
        assert tuple(record) == iface.design.INGESTION_RESULT_FIELDS
        iface.design.validate_ingestion_result(record)
    for record in response["new_authority_records"]:
        assert tuple(record) == iface.design.AUTHORITY_RECORD_FIELDS
        iface.design.validate_authority_record(record)


def test_result_input_order_and_batch_atomicity(truth_cases):
    case = _case(truth_cases, "atomicity_rollback_blocked")
    response = _evaluate(case)
    assert [
        row["sample_index_row_id"]
        for row in response["ingestion_result_records"]
    ] == [review["sample_index_row_id"] for review, _ in case.submissions]
    assert response["batch_passed"] is False
    assert response["new_authority_records"] == ()
    assert all(
        row["outcome"] != "passed"
        and row["consumed_review_record"] is False
        and row["consumed_ingestion_envelope"] is False
        and row["authority_disposition"] == ""
        and row["authority_record_sha256"] == ""
        for row in response["ingestion_result_records"]
    )


def test_non_replay_new_authority_linkage_and_uniqueness(truth_cases):
    response = _evaluate(_case(truth_cases, "valid_partial_two_sample_batch"))
    authorities = {
        row["authority_record_sha256"]: row
        for row in response["new_authority_records"]
    }
    assert len(authorities) == len(response["new_authority_records"]) == 2
    assert len({
        row["sample_index_row_id"]
        for row in response["new_authority_records"]
    }) == 2
    for result in response["ingestion_result_records"]:
        assert result["idempotent_replay"] is False
        authority = authorities[result["authority_record_sha256"]]
        assert authority["sample_index_row_id"] == result["sample_index_row_id"]
        assert (
            authority["source_review_record_sha256"]
            == result["review_record_sha256"]
        )
        assert authority["review_decision"] == result["review_decision"]


def test_replay_maps_only_to_valid_existing_authority(truth_cases):
    initial_case = _case(truth_cases, "valid_select")
    initial = _evaluate(initial_case)
    authority = dict(initial["new_authority_records"][0])
    review = initial_case.submissions[0][0]
    envelope = iface._synthetic_envelope(review, "synthetic-replay")
    submissions = ((review, envelope),)
    response = iface.evaluate_current11_warhead_boundary_review_ingestion_v1(
        submissions=submissions,
        authority_context=initial_case.authority_context,
        existing_authorities=(authority,),
    )
    assert response["batch_passed"] is True
    assert response["new_authority_records"] == ()
    result = response["ingestion_result_records"][0]
    assert result["idempotent_replay"] is True
    assert result["reason"] == "IDEMPOTENT_REPLAY"
    assert result["authority_record_sha256"] == authority[
        "authority_record_sha256"
    ]
    assert result["sample_index_row_id"] == authority["sample_index_row_id"]
    assert (
        result["review_record_sha256"]
        == authority["source_review_record_sha256"]
    )


def test_evaluator_integrity_failure_prevents_design_ingest(
    monkeypatch, truth_cases,
):
    case = _case(truth_cases, "valid_quarantine")
    ingest_calls = []

    def integrity_failure():
        raise ValueError("runtime integrity sentinel")

    def forbidden_ingest(*args, **kwargs):
        ingest_calls.append((args, kwargs))
        raise AssertionError("design ingest was reached")

    monkeypatch.setattr(
        iface,
        "_validate_public_evaluator_runtime_integrity_v1",
        integrity_failure,
    )
    monkeypatch.setattr(
        iface.design, "ingest_review_batch", forbidden_ingest,
    )
    with pytest.raises(ValueError, match="^runtime integrity sentinel$"):
        _evaluate(case)
    assert ingest_calls == []


def test_evaluator_integrity_precedes_exactly_one_design_ingest(
    monkeypatch, truth_cases,
):
    case = _case(truth_cases, "valid_quarantine")
    original_integrity = (
        iface._validate_public_evaluator_runtime_integrity_v1
    )
    original_ingest = iface.design.ingest_review_batch
    calls = []

    def integrity():
        calls.append(("integrity", (), {}))
        return original_integrity()

    def ingest(*args, **kwargs):
        calls.append(("ingest", args, kwargs))
        return original_ingest(*args, **kwargs)

    monkeypatch.setattr(
        iface, "_validate_public_evaluator_runtime_integrity_v1", integrity,
    )
    monkeypatch.setattr(iface.design, "ingest_review_batch", ingest)
    response = _evaluate(case)
    assert response["batch_passed"] is True
    assert [call[0] for call in calls] == ["integrity", "ingest"]
    _, args, kwargs = calls[1]
    assert args == (case.submissions,)
    assert kwargs == {
        "authority_context": case.authority_context,
        "existing_authorities": case.existing_authorities,
    }


def test_inputs_unmodified_and_byte_deterministic(truth_cases):
    case = _case(truth_cases, "valid_partial_two_sample_batch")
    before = copy.deepcopy((
        case.submissions, case.authority_context, case.existing_authorities,
    ))
    first = _evaluate(case)
    second = _evaluate(case)
    after = (
        case.submissions, case.authority_context, case.existing_authorities,
    )
    assert after == before
    first_bytes = iface.canonical_json(
        iface._response_hash_payload(first)
    ).encode()
    second_bytes = iface.canonical_json(
        iface._response_hash_payload(second)
    ).encode()
    assert first == second
    assert first_bytes == second_bytes


def test_evaluator_has_no_filesystem_side_effects(tmp_path, truth_cases):
    case = _case(truth_cases, "valid_quarantine")
    before = tuple(tmp_path.iterdir())
    prior = Path.cwd()
    os.chdir(tmp_path)
    try:
        response = _evaluate(case)
    finally:
        os.chdir(prior)
    assert response["batch_passed"] is True
    assert tuple(tmp_path.iterdir()) == before == ()


@pytest.mark.parametrize(
    ("mutation", "reason"),
    (
        ("field_inventory", "INTERFACE_RESPONSE_FIELD_INVENTORY_MISMATCH"),
        ("tuple_type", "INTERFACE_RESPONSE_EXACT_TYPE_INVALID"),
        ("version", "INTERFACE_RESPONSE_VERSION_MISMATCH"),
        ("context_sha", "AUTHORITY_CONTEXT_DIGEST_LINKAGE_MISMATCH"),
        ("response_sha", "INTERFACE_RESPONSE_SHA_MISMATCH"),
        ("result_count", "INTERFACE_RESULT_COUNT_MISMATCH"),
        ("result_order", "INTERFACE_RESULT_INPUT_ORDER_MISMATCH"),
        ("batch_passed", "INTERFACE_BATCH_PASSED_INVARIANT_MISMATCH"),
        ("invalid_result", "INTERFACE_INGESTION_RESULT_INVALID"),
        ("invalid_authority", "INTERFACE_NEW_AUTHORITY_INVALID"),
    ),
)
def test_response_validator_fail_closed_mutations(
    truth_cases, mutation, reason,
):
    case = _case(truth_cases, "valid_partial_two_sample_batch")
    response = copy.deepcopy(_evaluate(case))
    if mutation == "field_inventory":
        response["extra"] = ""
    elif mutation == "tuple_type":
        response["ingestion_result_records"] = list(
            response["ingestion_result_records"]
        )
    elif mutation == "version":
        response["interface_response_version"] = "forged"
    elif mutation == "context_sha":
        response["authority_context_record_sha256"] = "0" * 64
    elif mutation == "response_sha":
        response["interface_response_sha256"] = "0" * 64
    elif mutation == "result_count":
        response["ingestion_result_records"] = (
            response["ingestion_result_records"][:-1]
        )
    elif mutation == "result_order":
        response["ingestion_result_records"] = tuple(
            reversed(response["ingestion_result_records"])
        )
    elif mutation == "batch_passed":
        response["batch_passed"] = False
    elif mutation == "invalid_result":
        record = dict(response["ingestion_result_records"][0])
        record["passed"] = False
        response["ingestion_result_records"] = (
            record, *response["ingestion_result_records"][1:],
        )
    else:
        record = dict(response["new_authority_records"][0])
        record["authority_record_sha256"] = "0" * 64
        response["new_authority_records"] = (
            record, *response["new_authority_records"][1:],
        )
    if mutation not in {
        "field_inventory", "tuple_type", "version", "context_sha",
        "response_sha",
    }:
        _rehash_response(response)
    with pytest.raises(ValueError, match=reason):
        _validate(response, case)


def test_validator_failed_batch_cannot_emit_authority(truth_cases):
    failed_case = _case(truth_cases, "not_reviewed_blocked")
    failed = copy.deepcopy(_evaluate(failed_case))
    passed = _evaluate(_case(truth_cases, "valid_quarantine"))
    failed["new_authority_records"] = passed["new_authority_records"]
    _rehash_response(failed)
    with pytest.raises(ValueError, match="INTERFACE_FAILED_BATCH_EFFECT_MISMATCH"):
        _validate(failed, failed_case)


def test_exact12_contract_registry(build_result):
    assert tuple(build_result.contract_rows[0]) == iface.CONTRACT_COLUMNS
    assert [row["contract_id"] for row in build_result.contract_rows] == [
        f"IFACE_{index:03d}" for index in range(1, 13)
    ]
    assert all(
        row["fails_closed"] is True and row["verified"] is True
        for row in build_result.contract_rows
    )
    assert "IFACE_013" not in {
        row["contract_id"] for row in build_result.contract_rows
    }


def test_exact18_truth_matrix_order_counts_and_zero_writes(build_result):
    expected = [
        "valid_select",
        "valid_revise",
        "valid_quarantine",
        "valid_partial_two_sample_batch",
        "not_reviewed_blocked",
        "conflicting_reingestion_blocked",
        "atomicity_rollback_blocked",
        "mixed_batch_ids_invalid",
        "duplicate_sample_invalid",
        "duplicate_review_sha_invalid",
        "forged_authority_context_invalid",
        "forged_review_identity_invalid",
        "ineligible_select_invalid",
        "invalid_envelope_exact_type",
        "invalid_existing_authority_hash",
        "invalid_existing_authority_decision_evidence",
        "empty_batch_invalid",
        "oversized_batch_invalid",
    ]
    assert [row["truth_case_name"] for row in build_result.truth_rows] == expected
    assert len(build_result.truth_rows) == 18
    assert sum(
        row["expected_outcome_class"] == "passed"
        for row in build_result.truth_rows
    ) == 4
    assert sum(
        row["expected_outcome_class"] == "blocked"
        for row in build_result.truth_rows
    ) == 3
    assert sum(
        row["expected_outcome_class"] == "invalid"
        for row in build_result.truth_rows
    ) == 11
    assert all(
        row["verified"] is True and row["filesystem_write_count"] == 0
        for row in build_result.truth_rows
    )


def test_exact11_readiness_current_truth(build_result):
    assert len(build_result.readiness_rows) == 11
    assert [
        row["sample_index_row_id"] for row in build_result.readiness_rows
    ] == sorted(
        row["sample_index_row_id"] for row in build_result.readiness_rows
    )
    for row in build_result.readiness_rows:
        assert row["review_package_available"] is True
        assert row["blank_review_template_available"] is True
        assert row["interface_implementation_available"] is True
        assert row["immutable_authority_context_available"] is True
        assert row["interface_synthetic_validation_passed"] is True
        for field in (
            "completed_review_record_available",
            "human_provenance_envelope_available",
            "ready_for_real_ingestion_execution",
            "real_ingestion_completed",
            "authority_record_available",
            "complete_warhead_atom_set_authority_available",
            "exact_one_attachment_boundary_authority_available",
            "sample_quarantined",
            "ready_for_candidate_warhead_smarts_materialization",
            "ready_for_role_proposal_generation",
            "ready_for_mask_materialization",
            "ready_for_model_integration",
            "ready_for_training",
        ):
            assert row[field] is False
        assert set(row["blocking_reasons"].split(";")) >= {
            "completed_human_review_record_missing",
            "human_provenance_envelope_missing",
            "real_ingestion_not_executed",
        }


def test_exact35_frozen_typed_unique_failure_mutations(build_result):
    assert is_dataclass(iface.InterfaceScenario)
    assert iface.InterfaceScenario.__dataclass_params__.frozen is True
    assert len(fields(iface.InterfaceScenario)) == 35
    assert len(iface.FAILURE_MUTATIONS) == len(build_result.failure_rows) == 35
    baseline = iface.InterfaceScenario()
    signatures = []
    for mutation, row in zip(
        iface.FAILURE_MUTATIONS, build_result.failure_rows,
    ):
        _, field, value, expected = mutation
        assert type(value) is type(getattr(baseline, field))
        assert value != getattr(baseline, field)
        observed = iface.observe_failure_scenario(
            replace(baseline, **{field: value})
        )
        assert observed == (expected,)
        assert row["expected_reason_verified"] is True
        assert row["fails_closed"] is True
        assert row["contract_row_count"] == 0
        assert row["truth_row_count"] == 0
        assert row["current11_readiness_row_count"] == 0
        assert row["actual_completed_review_count"] == 0
        assert row["actual_ingestion_envelope_count"] == 0
        assert row["actual_ingestion_result_count"] == 0
        assert row["actual_authority_record_count"] == 0
        assert row["training_ready"] is False
        assert row["verified"] is True
        signatures.append(row["mutation_signature"])
    assert len(signatures) == len(set(signatures))


def test_transaction_is_all_or_nothing():
    baseline = iface.transaction_tables(iface.InterfaceScenario())
    assert [len(table) for table in baseline] == [12, 18, 11]
    for _, field, value, _ in iface.FAILURE_MUTATIONS:
        scenario = replace(iface.InterfaceScenario(), **{field: value})
        assert iface.transaction_tables(scenario) == ((), (), ())


def test_manifest_exact_counts_boundary_and_next_step():
    manifest = json.loads(
        (ROOT / iface.OUTPUT_ROOT / iface.MANIFEST_FILE).read_bytes()
    )
    assert manifest["source_count"] == 6
    assert manifest["design_interface_ready"] is True
    assert manifest["design_execution_ready"] is False
    assert manifest["interface_response_field_count"] == 6
    assert manifest["interface_response_fields"] == list(
        iface.INTERFACE_RESPONSE_FIELDS
    )
    assert manifest["interface_response_hash_included_field_count"] == 5
    assert manifest["contract_count"] == 12
    assert manifest["truth_case_count"] == 18
    assert (
        manifest["truth_passed_case_count"],
        manifest["truth_blocked_case_count"],
        manifest["truth_invalid_case_count"],
    ) == (4, 3, 11)
    assert manifest["current11_readiness_row_count"] == 11
    assert manifest["interface_implementation_completed"] is True
    assert manifest["ready_for_synthetic_interface_evaluation"] is True
    assert manifest["ready_for_real_review_ingestion_execution"] is False
    assert manifest["transaction_succeeded"] is True
    assert manifest["failure_mutation_count"] == 35
    assert manifest["failure_mutations_all_fail_closed"] is True
    assert manifest["supported_runtime_lifecycles"] == list(
        iface.SUPPORTED_RUNTIME_LIFECYCLES
    )
    assert manifest["formal_successor_runtime_compatible"] is True
    assert manifest["runtime_lifecycle_count"] == 4
    assert manifest["runtime_lifecycles_all_verified"] is True
    assert manifest["public_runtime_compatibility_scope"] == (
        iface.PUBLIC_RUNTIME_COMPATIBILITY_SCOPE
    )
    assert manifest["public_runtime_required_base_commit"] == iface.BASE_COMMIT
    assert manifest["artifact_build_lifecycle_strict"] is True
    assert manifest["public_runtime_requires_exact_interface_lifecycle"] is False
    assert manifest["downstream_descendant_runtime_compatible"] is True
    assert manifest["downstream_descendant_depths_verified"] == [1, 2]
    assert manifest["imported_design_source_integrity_required"] is True
    assert manifest["imported_design_source_sha256"] == (
        iface.IMPORTED_DESIGN_SOURCE_SHA256
    )
    assert manifest["working_tree_design_source_must_match_HEAD"] is True
    assert (
        manifest["downstream_callers_must_not_call_interface_build_result"]
        is True
    )
    assert manifest["public_evaluator_runtime_repository_guard_required"] is True
    assert manifest["public_evaluator_design_source_integrity_required"] is True
    assert (
        manifest[
            "public_evaluator_repository_root_inferred_from_interface_module"
        ]
        is True
    )
    assert (
        manifest[
            "public_evaluator_calls_design_ingest_only_after_integrity_validation"
        ]
        is True
    )
    assert manifest["saved_context_cannot_bypass_design_source_integrity"] is True
    assert manifest["business_payload_in_memory_only"] is True
    assert manifest["public_runtime_integrity_checks_read_only"] is True
    assert manifest["filesystem_persistence_allowed"] is False
    assert manifest["separate_design_base_worktree_required"] is False
    assert (
        manifest["authority_context_built_from_design_base_git_objects"]
        is True
    )
    assert manifest["design_lifecycle_bound_builder_called"] is False
    assert manifest["design_lifecycle_bound_build_result_called"] is False
    assert manifest["canonical_masks"] == list(iface.CANONICAL_MASKS)
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["ready_for_training"] is False
    assert manifest["formal_training_prerequisite"] == "feature-semantics audit"
    assert manifest["Step12D_scope"] == "smoke legality check only"
    assert manifest["recommended_engineering_next_step"] == (
        "design_covapie_current11_warhead_atom_set_and_attachment_"
        "boundary_review_submission_adapter_v1"
    )
    assert iface.MANIFEST_FILE not in manifest["output_sha256"]


def test_materialization_byte_determinism_and_committed_files_match():
    first = iface.build_evidence_payloads(ROOT)
    second = iface.build_evidence_payloads(ROOT)
    assert first == second
    assert tuple(first) == iface.OUTPUT_FILES
    for name, payload in first.items():
        assert (ROOT / iface.OUTPUT_ROOT / name).read_bytes() == payload


def test_isolated_production_import_silent_and_side_effect_free(tmp_path):
    code = (
        "from covalent_ext import "
        "covapie_current11_warhead_atom_set_and_attachment_boundary_"
        "review_ingestion_interface_v1"
    )
    result = subprocess.run(
        (sys.executable, "-B", "-c", code),
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == b""
    assert result.stderr == b""
    assert tuple(tmp_path.iterdir()) == ()


def test_exact10_filesystem_safety_and_no_lifecycle_artifacts():
    assert len(iface.EXACT10_PATHS) == 10
    for path in iface.EXACT10_PATHS:
        target = ROOT / path
        info = target.lstat()
        assert stat.S_ISREG(info.st_mode)
        assert not target.is_symlink()
        assert not info.st_mode & stat.S_IXUSR
        assert info.st_size < 5 * 1024 * 1024
        assert target.suffix not in FORBIDDEN_SUFFIXES
    names = {
        path.name.lower() for path in (ROOT / iface.OUTPUT_ROOT).iterdir()
    }
    for token in (
        "completed_review", "ingestion_envelope", "ingestion_result",
        "authority_record", "smarts",
    ):
        assert not any(token in name for name in names)


def test_test_and_checker_sources_have_no_second_worktree_dependency():
    forbidden = (
        "design" + "_compatible_worktree",
        "_design" + "_compatible_worktree",
        "DESIGN" + "_REPO",
        "design-compatible BASE worktree is " + "unavailable",
    )
    for path in (
        Path(__file__),
        ROOT
        / "scripts"
        / "check_covapie_current11_warhead_atom_set_and_attachment_"
        "boundary_review_ingestion_interface_v1.py",
    ):
        source = path.read_text(encoding="utf-8")
        assert all(token not in source for token in forbidden)


def _runtime_git(repository: Path, *arguments: str, env=None):
    result = subprocess.run(
        ("git", *arguments),
        cwd=repository,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    return result


def _single_worktree_runtime_probe(repository: Path, expected: str):
    code = r'''
import copy, hashlib, subprocess
from pathlib import Path
from covalent_ext import covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1 as iface
root = Path.cwd()
def status():
    return subprocess.run(("git", "status", "--porcelain=v1", "--untracked-files=all"), cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
def evidence():
    output = root / iface.OUTPUT_ROOT
    return tuple((path.name, hashlib.sha256(path.read_bytes()).hexdigest()) for path in sorted(output.iterdir()) if path.is_file())
before_status = status()
before_evidence = evidence()
context = iface.build_current11_warhead_boundary_review_ingestion_authority_context_v1(root)
iface.design.validate_ingestion_authority_context(context)
built = iface.build_result(root)
assert built.transaction_succeeded and not built.blocking_reasons
assert built.actual_lifecycle == EXPECTED
assert built.design_evidence is not None
case = next(case for case in iface._build_synthetic_truth_cases(built.design_evidence) if case.name == "valid_quarantine")
before_inputs = copy.deepcopy((case.submissions, case.authority_context, case.existing_authorities))
response = iface.evaluate_current11_warhead_boundary_review_ingestion_v1(submissions=case.submissions, authority_context=case.authority_context, existing_authorities=case.existing_authorities)
iface.validate_current11_warhead_boundary_review_ingestion_interface_response_v1(response, submissions=case.submissions, authority_context=case.authority_context, existing_authorities=case.existing_authorities)
assert response["batch_passed"] is True
assert len(response["new_authority_records"]) == 1
assert (case.submissions, case.authority_context, case.existing_authorities) == before_inputs
assert status() == before_status
assert evidence() == before_evidence
'''
    code = "EXPECTED = " + repr(expected) + "\n" + code
    result = subprocess.run(
        (sys.executable, "-B", "-c", code),
        cwd=repository,
        env={
            **os.environ,
            "PYTHONPATH": "src",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert result.stdout == b""
    assert result.stderr == b""
    worktrees = _runtime_git(
        repository, "worktree", "list", "--porcelain",
    ).stdout.decode().splitlines()
    assert sum(line.startswith("worktree ") for line in worktrees) == 1


def _single_worktree_descendant_probe(repository: Path, expected_depth: int):
    code = r'''
import copy, hashlib, subprocess
from pathlib import Path
from covalent_ext import covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1 as iface
root = Path.cwd()
def status():
    return subprocess.run(("git", "status", "--porcelain=v1", "--untracked-files=all"), cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
def evidence():
    output = root / iface.OUTPUT_ROOT
    return tuple((path.name, hashlib.sha256(path.read_bytes()).hexdigest()) for path in sorted(output.iterdir()) if path.is_file())
before_status = status()
before_evidence = evidence()
assert subprocess.run(("git", "merge-base", "--is-ancestor", iface.BASE_COMMIT, "HEAD"), cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False).returncode == 0
context = iface.build_current11_warhead_boundary_review_ingestion_authority_context_v1(root)
iface.design.validate_ingestion_authority_context(context)
design_evidence = iface._committed_design_interface_evidence(context)
case = next(case for case in iface._build_synthetic_truth_cases(design_evidence) if case.name == "valid_quarantine")
before_inputs = copy.deepcopy((case.submissions, case.authority_context, case.existing_authorities))
response = iface.evaluate_current11_warhead_boundary_review_ingestion_v1(submissions=case.submissions, authority_context=case.authority_context, existing_authorities=case.existing_authorities)
iface.validate_current11_warhead_boundary_review_ingestion_interface_response_v1(response, submissions=case.submissions, authority_context=case.authority_context, existing_authorities=case.existing_authorities)
assert response["batch_passed"] is True
assert len(response["new_authority_records"]) == 1
assert (case.submissions, case.authority_context, case.existing_authorities) == before_inputs
assert status() == before_status
assert evidence() == before_evidence
assert DEPTH in (1, 2)
'''
    result = subprocess.run(
        (
            sys.executable, "-B", "-c",
            "DEPTH = " + repr(expected_depth) + "\n" + code,
        ),
        cwd=repository,
        env={
            **os.environ,
            "PYTHONPATH": "src",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert result.stdout == b""
    assert result.stderr == b""
    worktrees = _runtime_git(
        repository, "worktree", "list", "--porcelain",
    ).stdout.decode().splitlines()
    assert sum(line.startswith("worktree ") for line in worktrees) == 1


def _public_builder_failure(
    repository: Path, expected_reason: str,
    repo_argument: str = ".",
):
    code = r'''
from pathlib import Path
from covalent_ext import covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1 as iface
try:
    iface.build_current11_warhead_boundary_review_ingestion_authority_context_v1(Path(REPO_ARGUMENT))
except ValueError as error:
    assert str(error) == EXPECTED_REASON, str(error)
else:
    raise AssertionError("invalid public runtime repository was accepted")
'''
    result = subprocess.run(
        (
            sys.executable, "-B", "-c",
            "EXPECTED_REASON = " + repr(expected_reason) + "\n"
            + "REPO_ARGUMENT = " + repr(repo_argument) + "\n"
            + code,
        ),
        cwd=repository,
        env={
            **os.environ,
            "PYTHONPATH": "src",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert result.stdout == b""
    assert result.stderr == b""


def test_single_worktree_exact4_public_runtime_matrix(tmp_path):
    remote = tmp_path / "remote.git"
    repository = tmp_path / "repository"
    _runtime_git(tmp_path, "init", "--bare", str(remote))
    _runtime_git(
        remote,
        "fetch",
        str(ROOT),
        f"{iface.BASE_COMMIT}:refs/heads/main",
    )
    _runtime_git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
    _runtime_git(tmp_path, "clone", str(remote), str(repository))
    for path in iface.EXACT10_PATHS:
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / path, target)

    _single_worktree_runtime_probe(repository, "pre_commit")
    _runtime_git(
        repository, "add", "--",
        *(path.as_posix() for path in iface.EXACT10_PATHS),
    )
    commit_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "CovaPIE Runtime Test",
        "GIT_AUTHOR_EMAIL": "runtime-test@example.invalid",
        "GIT_COMMITTER_NAME": "CovaPIE Runtime Test",
        "GIT_COMMITTER_EMAIL": "runtime-test@example.invalid",
        "GIT_AUTHOR_DATE": "2000-01-01T00:00:00+00:00",
        "GIT_COMMITTER_DATE": "2000-01-01T00:00:00+00:00",
    }
    _runtime_git(
        repository,
        "commit",
        "-m",
        iface.FORMAL_COMMIT_SUBJECT,
        env=commit_env,
    )
    candidate = _runtime_git(
        repository, "rev-parse", "HEAD",
    ).stdout.decode().strip()

    _runtime_git(repository, "checkout", "--detach", candidate)
    _single_worktree_runtime_probe(
        repository, "detached_candidate_post_commit",
    )
    _runtime_git(repository, "checkout", "-B", "main", candidate)
    _single_worktree_runtime_probe(
        repository, "formal_main_post_commit_unpushed",
    )
    _runtime_git(repository, "push", "origin", "main")
    _single_worktree_runtime_probe(repository, "formal_main_post_push")

    for depth in (1, 2):
        unrelated = (
            repository / "docs"
            / f"synthetic-downstream-descendant-depth-{depth}.txt"
        )
        unrelated.write_text(
            f"synthetic downstream descendant depth {depth}\n",
            encoding="utf-8",
        )
        _runtime_git(
            repository, "add", "--",
            unrelated.relative_to(repository).as_posix(),
        )
        _runtime_git(
            repository,
            "commit",
            "-m",
            f"synthetic downstream descendant depth {depth}",
            env=commit_env,
        )
        _single_worktree_descendant_probe(repository, depth)
    assert iface.SUPPORTED_RUNTIME_LIFECYCLES == lifecycle.LIFECYCLES


def test_saved_context_cannot_bypass_evaluator_design_integrity(tmp_path):
    remote = tmp_path / "remote.git"
    repository = tmp_path / "repository"
    _runtime_git(tmp_path, "init", "--bare", str(remote))
    _runtime_git(
        remote,
        "fetch",
        str(ROOT),
        f"{iface.BASE_COMMIT}:refs/heads/main",
    )
    _runtime_git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
    _runtime_git(tmp_path, "clone", str(remote), str(repository))
    for path in iface.EXACT10_PATHS:
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / path, target)
    _runtime_git(
        repository, "add", "--",
        *(path.as_posix() for path in iface.EXACT10_PATHS),
    )
    commit_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "CovaPIE Saved Context Runtime Test",
        "GIT_AUTHOR_EMAIL": "saved-context-runtime@example.invalid",
        "GIT_COMMITTER_NAME": "CovaPIE Saved Context Runtime Test",
        "GIT_COMMITTER_EMAIL": "saved-context-runtime@example.invalid",
        "GIT_AUTHOR_DATE": "2000-01-03T00:00:00+00:00",
        "GIT_COMMITTER_DATE": "2000-01-03T00:00:00+00:00",
    }
    _runtime_git(
        repository,
        "commit",
        "-m",
        iface.FORMAL_COMMIT_SUBJECT,
        env=commit_env,
    )
    unrelated = repository / "docs" / "saved-context-descendant.txt"
    unrelated.write_text(
        "saved context legal descendant\n", encoding="utf-8",
    )
    _runtime_git(
        repository, "add", "--",
        unrelated.relative_to(repository).as_posix(),
    )
    _runtime_git(
        repository,
        "commit",
        "-m",
        "saved context legal descendant",
        env=commit_env,
    )
    code = r'''
import copy, subprocess
from pathlib import Path
from covalent_ext import covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1 as iface
root = Path.cwd()
def status():
    return subprocess.run(("git", "status", "--porcelain=v1", "--untracked-files=all"), cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
context = iface.build_current11_warhead_boundary_review_ingestion_authority_context_v1(root)
evidence = iface._committed_design_interface_evidence(context)
case = next(case for case in iface._build_synthetic_truth_cases(evidence) if case.name == "valid_quarantine")
saved_inputs = copy.deepcopy((case.submissions, context, ()))
original_ingest = iface.design.ingest_review_batch
ingest_calls = []
def recording_ingest(*args, **kwargs):
    ingest_calls.append((args, kwargs))
    return original_ingest(*args, **kwargs)
iface.design.ingest_review_batch = recording_ingest
design_source = root / iface.DESIGN_PRODUCTION
frozen = design_source.read_bytes()
design_source.write_bytes(frozen + b"\n# uncommitted evaluator integrity probe\n")
before_status = status()
before_calls = len(ingest_calls)
failed_authorities = []
try:
    iface.evaluate_current11_warhead_boundary_review_ingestion_v1(submissions=case.submissions, authority_context=context, existing_authorities=())
except ValueError as error:
    assert str(error) == "INTERFACE_IMPORTED_DESIGN_SOURCE_INTEGRITY_INVALID"
else:
    raise AssertionError("uncommitted saved-context drift was accepted")
assert len(ingest_calls) == before_calls
assert failed_authorities == []
assert status() == before_status
design_source.write_bytes(frozen)
restored = iface.evaluate_current11_warhead_boundary_review_ingestion_v1(submissions=case.submissions, authority_context=context, existing_authorities=())
assert restored["batch_passed"] is True
assert len(restored["new_authority_records"]) == 1
design_source.write_bytes(frozen + b"\n# committed evaluator integrity probe\n")
subprocess.run(("git", "add", "--", iface.DESIGN_PRODUCTION.as_posix()), cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
subprocess.run(("git", "commit", "-m", "committed evaluator integrity probe"), cwd=root, env=COMMIT_ENV, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
before_status = status()
before_calls = len(ingest_calls)
failed_authorities = []
try:
    iface.evaluate_current11_warhead_boundary_review_ingestion_v1(submissions=case.submissions, authority_context=context, existing_authorities=())
except ValueError as error:
    assert str(error) == "INTERFACE_IMPORTED_DESIGN_SOURCE_INTEGRITY_INVALID"
else:
    raise AssertionError("committed saved-context drift was accepted")
assert len(ingest_calls) == before_calls
assert failed_authorities == []
assert status() == before_status
design_source.write_bytes(frozen)
subprocess.run(("git", "add", "--", iface.DESIGN_PRODUCTION.as_posix()), cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
subprocess.run(("git", "commit", "-m", "restore frozen design source"), cwd=root, env=COMMIT_ENV, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
restored_again = iface.evaluate_current11_warhead_boundary_review_ingestion_v1(submissions=case.submissions, authority_context=context, existing_authorities=())
assert restored_again == restored
assert len(restored_again["new_authority_records"]) == 1
assert (case.submissions, context, ()) == saved_inputs
'''
    result = subprocess.run(
        (
            sys.executable, "-B", "-c",
            "COMMIT_ENV = " + repr(commit_env) + "\n" + code,
        ),
        cwd=repository,
        env={
            **os.environ,
            "PYTHONPATH": "src",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert result.stdout == b""
    assert result.stderr == b""
    worktrees = _runtime_git(
        repository, "worktree", "list", "--porcelain",
    ).stdout.decode().splitlines()
    assert sum(line.startswith("worktree ") for line in worktrees) == 1


def test_single_worktree_invalid_descendants_fail_closed(tmp_path):
    remote = tmp_path / "remote.git"
    repository = tmp_path / "repository"
    _runtime_git(tmp_path, "init", "--bare", str(remote))
    _runtime_git(
        remote,
        "fetch",
        str(ROOT),
        f"{iface.BASE_COMMIT}:refs/heads/main",
    )
    _runtime_git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
    _runtime_git(tmp_path, "clone", str(remote), str(repository))
    for path in iface.EXACT10_PATHS:
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / path, target)
    _runtime_git(
        repository, "add", "--",
        *(path.as_posix() for path in iface.EXACT10_PATHS),
    )
    commit_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "CovaPIE Invalid Runtime Test",
        "GIT_AUTHOR_EMAIL": "invalid-runtime-test@example.invalid",
        "GIT_COMMITTER_NAME": "CovaPIE Invalid Runtime Test",
        "GIT_COMMITTER_EMAIL": "invalid-runtime-test@example.invalid",
        "GIT_AUTHOR_DATE": "2000-01-01T00:00:00+00:00",
        "GIT_COMMITTER_DATE": "2000-01-01T00:00:00+00:00",
    }
    _runtime_git(
        repository,
        "commit",
        "-m",
        iface.FORMAL_COMMIT_SUBJECT,
        env=commit_env,
    )
    candidate = _runtime_git(
        repository, "rev-parse", "HEAD",
    ).stdout.decode().strip()

    tree = _runtime_git(
        repository, "rev-parse", f"{candidate}^{{tree}}",
    ).stdout.decode().strip()
    unrelated = _runtime_git(
        repository, "commit-tree", tree,
        env={
            **commit_env,
            "GIT_AUTHOR_DATE": "2000-01-02T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2000-01-02T00:00:00+00:00",
        },
    ).stdout.decode().strip()
    _runtime_git(repository, "checkout", "--detach", unrelated)
    _public_builder_failure(
        repository, "INTERFACE_PUBLIC_RUNTIME_REPOSITORY_INVALID",
    )

    _runtime_git(repository, "checkout", "--detach", candidate)
    design_source = repository / iface.DESIGN_PRODUCTION
    frozen_payload = design_source.read_bytes()
    design_source.write_bytes(frozen_payload + b"\n# uncommitted integrity probe\n")
    _public_builder_failure(
        repository,
        "INTERFACE_IMPORTED_DESIGN_SOURCE_INTEGRITY_INVALID",
    )
    design_source.write_bytes(frozen_payload)
    design_source.write_bytes(frozen_payload + b"\n# committed integrity probe\n")
    _runtime_git(
        repository, "add", "--", iface.DESIGN_PRODUCTION.as_posix(),
    )
    _runtime_git(
        repository,
        "commit",
        "-m",
        "synthetic descendant modifies frozen design source",
        env=commit_env,
    )
    _public_builder_failure(
        repository,
        "INTERFACE_IMPORTED_DESIGN_SOURCE_INTEGRITY_INVALID",
    )


def test_shared_hermetic_lifecycle_exact4_and_cleanup(tmp_path):
    report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
        ROOT,
        tmp_path,
        base_commit=iface.BASE_COMMIT,
        formal_commit_subject=iface.FORMAL_COMMIT_SUBJECT,
        exact_paths=iface.EXACT10_PATHS,
    )
    assert report.base_commit == iface.BASE_COMMIT
    assert report.candidate_parent == iface.BASE_COMMIT
    assert report.candidate_subject == iface.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert report.cleanup_verified is True
    assert [
        report.pre_commit.lifecycle,
        report.detached_candidate_post_commit.lifecycle,
        report.formal_main_post_commit_unpushed.lifecycle,
        report.formal_main_post_push.lifecycle,
    ] == list(lifecycle.LIFECYCLES)
    assert tuple(tmp_path.iterdir()) == ()
