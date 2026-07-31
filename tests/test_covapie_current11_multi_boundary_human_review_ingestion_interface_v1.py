from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence, get_type_hints

import pytest

from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_contract_design_v1
    as design,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_interface_v1
    as public_interface,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_submission_adapter_v1
    as adapter,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(
    "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/"
    "covapie-envs/diffsbdd-legacy-test-v1/bin/python3.10"
)
PUBLIC_FUNCTION = (
    public_interface
    .evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1
)


def _load_checker():
    path = (
        REPO_ROOT
        / "scripts/check_covapie_current11_multi_boundary_"
        "human_review_ingestion_interface_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "multi_boundary_ingestion_interface_checker_for_tests", path,
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


CHECKER = _load_checker()


@pytest.fixture(scope="session")
def synthetic_case() -> tuple[bytes, bytes, bytes, bytes]:
    return CHECKER._synthetic_case(REPO_ROOT)


@pytest.fixture(scope="session")
def fresh_private_response(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> dict[str, Any]:
    return CHECKER._private_evaluate(REPO_ROOT, synthetic_case)


def _public(
    case: tuple[bytes, bytes, bytes, bytes],
    *,
    existing: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    return CHECKER._public_evaluate(
        REPO_ROOT, case, existing=existing,
    )


def _private(
    case: tuple[bytes, bytes, bytes, bytes],
    *,
    existing: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    multi_submission, adapter_response, v1_submission, v1_execution = case
    return design._reference_evaluate_covapie_current11_multi_boundary_ingestion_v1(
        adapter_response_payload=adapter_response,
        source_multi_boundary_submission_bundle=multi_submission,
        source_v1_submission_bundle=v1_submission,
        source_v1_ingestion_execution_bundle=v1_execution,
        repo_root=REPO_ROOT,
        existing_multi_boundary_authority_records=existing,
    )


def _canonical_sha(record: dict[str, Any], excluded: str) -> str:
    return hashlib.sha256(json.dumps(
        {key: value for key, value in record.items() if key != excluded},
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def _ordered_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _reviewed_graph_failure_case(
    case: tuple[bytes, bytes, bytes, bytes],
) -> tuple[bytes, bytes, bytes, bytes]:
    bundle = json.loads(case[0])
    item = bundle["submission_items"][2]
    item["reviewed_warhead_atom_ids"] = (
        item["reviewed_warhead_atom_ids"][:-1]
    )
    item["multi_boundary_review_record_sha256"] = _canonical_sha(
        item, "multi_boundary_review_record_sha256",
    )
    bundle["multi_boundary_submission_bundle_sha256"] = _canonical_sha(
        bundle, "multi_boundary_submission_bundle_sha256",
    )
    submission = _ordered_bytes(bundle)
    response = (
        adapter
        .adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1(
            source_payload=submission,
        )
    )
    return submission, _ordered_bytes(response), case[2], case[3]


def _assert_parity(
    case: tuple[bytes, bytes, bytes, bytes],
    *,
    existing: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    expected = _private(case, existing=existing)
    actual = _public(case, existing=existing)
    assert actual == expected
    assert actual is not expected
    design._validate_interface_response(actual)
    return actual


def _assert_atomic_reason(
    response: dict[str, Any],
    reason: str,
) -> None:
    assert response["batch_passed"] is False
    assert response["new_authority_records"] == ()
    reasons = [
        result["reason"]
        for result in response["ingestion_result_records"]
    ]
    assert reasons.count(reason) == 1
    assert reasons.count("BATCH_ATOMICITY_ABORTED") == 4


def test_public_api_signature_annotations_constants_and_design_sha() -> None:
    assert public_interface.__all__ == (
        "evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1",
    )
    assert public_interface.IMPLEMENTATION_VERSION == (
        "covapie_current11_multi_boundary_human_review_ingestion_interface_v1"
    )
    assert public_interface.DESIGN_COMMIT == (
        "bccd85194fbd19a55a77e998f5b9bcab5465b751"
    )
    assert public_interface.DESIGN_PRODUCTION_SHA256 == (
        "91899640e89cc462aac0a28245873da12ba573b8658a30e193da7ec9fac92771"
    )
    assert public_interface.PUBLIC_FUNCTION_NAME == PUBLIC_FUNCTION.__name__
    design_path = (
        REPO_ROOT
        / "src/covalent_ext/covapie_current11_multi_boundary_"
        "human_review_ingestion_contract_design_v1.py"
    )
    assert hashlib.sha256(design_path.read_bytes()).hexdigest() == (
        public_interface.DESIGN_PRODUCTION_SHA256
    )

    signature = inspect.signature(PUBLIC_FUNCTION)
    assert tuple(signature.parameters) == (
        "adapter_response_payload",
        "source_multi_boundary_submission_bundle",
        "source_v1_submission_bundle",
        "source_v1_ingestion_execution_bundle",
        "repo_root",
        "existing_multi_boundary_authority_records",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert signature.parameters[
        "existing_multi_boundary_authority_records"
    ].default == ()
    hints = get_type_hints(PUBLIC_FUNCTION)
    assert hints == {
        "adapter_response_payload": bytes,
        "source_multi_boundary_submission_bundle": bytes,
        "source_v1_submission_bundle": bytes,
        "source_v1_ingestion_execution_bundle": bytes,
        "repo_root": Path,
        "existing_multi_boundary_authority_records":
            Sequence[Mapping[str, Any]],
        "return": dict[str, Any],
    }


def test_import_is_silent() -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "from covalent_ext import "
            "covapie_current11_multi_boundary_human_review_"
            "ingestion_interface_v1",
        ],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == ""


def test_fresh_public_private_parity_and_exact_nested_contracts(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_private_response: dict[str, Any],
) -> None:
    response = _public(synthetic_case)
    assert response == fresh_private_response
    assert response is not fresh_private_response
    assert tuple(response) == (
        design.MULTI_BOUNDARY_INGESTION_INTERFACE_RESPONSE_FIELDS
    )
    assert len(response) == 6
    assert response["batch_passed"] is True
    assert len(response["ingestion_result_records"]) == 5
    assert len(response["new_authority_records"]) == 5
    for result in response["ingestion_result_records"]:
        assert tuple(result) == design.MULTI_BOUNDARY_INGESTION_RESULT_FIELDS
        assert len(result) == 18
        design._validate_result_record(result)
    for authority in response["new_authority_records"]:
        assert tuple(authority) == design.MULTI_BOUNDARY_AUTHORITY_RECORD_FIELDS
        assert len(authority) == 29
        design._validate_authority_record(authority)
    design._validate_interface_response(response)
    assert response[
        "multi_boundary_ingestion_interface_response_sha256"
    ] == CHECKER._EXPECTED_RESPONSE_SHA256


def test_full_replay_and_mixed_replay_preserve_private_semantics(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_private_response: dict[str, Any],
) -> None:
    authorities = fresh_private_response["new_authority_records"]
    full = _assert_parity(synthetic_case, existing=authorities)
    assert full["batch_passed"] is True
    assert full["new_authority_records"] == ()
    assert all(
        result["reason"] == "IDEMPOTENT_REPLAY"
        for result in full["ingestion_result_records"]
    )

    mixed = _assert_parity(synthetic_case, existing=authorities[:2])
    assert [
        result["reason"]
        for result in mixed["ingestion_result_records"]
    ] == [
        "IDEMPOTENT_REPLAY",
        "IDEMPOTENT_REPLAY",
        "PASSED",
        "PASSED",
        "PASSED",
    ]
    assert [
        record["sample_index_row_id"]
        for record in mixed["new_authority_records"]
    ] == [
        record["sample_index_row_id"] for record in authorities[2:]
    ]


def test_conflict_and_malformed_existing_authority_preserve_parity(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_private_response: dict[str, Any],
) -> None:
    conflict = copy.deepcopy(
        fresh_private_response["new_authority_records"][0]
    )
    conflict["review_notes_sha256"] = "f" * 64
    conflict["multi_boundary_authority_record_sha256"] = _canonical_sha(
        conflict, "multi_boundary_authority_record_sha256",
    )
    conflict_response = _assert_parity(
        synthetic_case, existing=(conflict,),
    )
    _assert_atomic_reason(
        conflict_response, "CONFLICTING_REVIEW_REINGESTION",
    )

    malformed_response = _assert_parity(
        synthetic_case,
        existing=({"authority_record_version": "legacy_exact_one_v1"},),
    )
    _assert_atomic_reason(
        malformed_response, "EXISTING_AUTHORITY_SET_INVALID",
    )
    assert all(
        result["reason"] != "CONFLICTING_REVIEW_REINGESTION"
        for result in malformed_response["ingestion_result_records"]
    )


def test_failed_adapter_and_v1_lineage_failures_preserve_parity(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    failed_adapter = (
        adapter
        .adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1(
            source_payload=b"{}",
        )
    )
    adapter_case = (
        synthetic_case[0],
        _ordered_bytes(failed_adapter),
        synthetic_case[2],
        synthetic_case[3],
    )
    adapter_response = _assert_parity(adapter_case)
    assert adapter_response["batch_passed"] is False
    assert adapter_response["new_authority_records"] == ()

    lineage_case = (
        synthetic_case[0],
        synthetic_case[1],
        synthetic_case[2],
        b"{}",
    )
    lineage_response = _assert_parity(lineage_case)
    _assert_atomic_reason(
        lineage_response, "SOURCE_V1_LINEAGE_MISMATCH",
    )


def test_reviewed_graph_failure_preserves_parity(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    response = _assert_parity(
        _reviewed_graph_failure_case(synthetic_case)
    )
    _assert_atomic_reason(
        response, "REVIEWED_GRAPH_INVARIANT_INVALID",
    )


def test_inputs_are_unchanged_and_calls_are_deterministic_and_isolated(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_private_response: dict[str, Any],
) -> None:
    input_snapshots = tuple(bytes(value) for value in synthetic_case)
    existing = [
        copy.deepcopy(fresh_private_response["new_authority_records"][0])
    ]
    existing_snapshot = copy.deepcopy(existing)
    first = _public(synthetic_case, existing=existing)
    second = _public(synthetic_case, existing=existing)
    assert first == second
    assert first is not second
    assert synthetic_case == input_snapshots
    assert existing == existing_snapshot
    assert first["ingestion_result_records"] is not (
        second["ingestion_result_records"]
    )
    assert first["new_authority_records"] is not (
        second["new_authority_records"]
    )

    second_snapshot = copy.deepcopy(second)
    first["new_authority_records"][0][
        "reviewed_warhead_atom_ids"
    ].append("__caller_mutation__")
    assert second == second_snapshot
    assert existing == existing_snapshot


def test_private_reference_is_called_exactly_once_per_public_call(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = (
        design._reference_evaluate_covapie_current11_multi_boundary_ingestion_v1
    )
    calls = 0

    def counted(*arguments, **keywords):
        nonlocal calls
        calls += 1
        return original(*arguments, **keywords)

    monkeypatch.setattr(
        design,
        "_reference_evaluate_covapie_current11_multi_boundary_ingestion_v1",
        counted,
    )
    _public(synthetic_case)
    assert calls == 1


def test_return_is_a_deep_copy_of_private_response(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_private_response: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cached_private = copy.deepcopy(fresh_private_response)
    cached_snapshot = copy.deepcopy(cached_private)
    monkeypatch.setattr(
        design,
        "_reference_evaluate_covapie_current11_multi_boundary_ingestion_v1",
        lambda **_keywords: cached_private,
    )
    response = _public(synthetic_case)
    assert response == cached_private
    assert response is not cached_private
    assert response["new_authority_records"][0] is not (
        cached_private["new_authority_records"][0]
    )
    assert response["new_authority_records"][0][
        "reviewed_warhead_atom_ids"
    ] is not cached_private["new_authority_records"][0][
        "reviewed_warhead_atom_ids"
    ]
    response["new_authority_records"][0][
        "reviewed_warhead_atom_ids"
    ].append("__deep_copy_probe__")
    assert cached_private == cached_snapshot


def test_malformed_private_response_raises_only_wrapper_invariant(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        design,
        "_reference_evaluate_covapie_current11_multi_boundary_ingestion_v1",
        lambda **_keywords: {},
    )
    with pytest.raises(ValueError) as captured:
        _public(synthetic_case)
    assert str(captured.value) == "INGESTION_RESPONSE_INVARIANT_INVALID"


def test_mutating_private_reference_raises_only_wrapper_invariant(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_private_response: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = [
        copy.deepcopy(fresh_private_response["new_authority_records"][0])
    ]
    calls = 0

    def mutating_reference(**keywords):
        nonlocal calls
        calls += 1
        keywords["existing_multi_boundary_authority_records"][0][
            "reviewer_id"
        ] = "__private_mutation__"
        return copy.deepcopy(fresh_private_response)

    monkeypatch.setattr(
        design,
        "_reference_evaluate_covapie_current11_multi_boundary_ingestion_v1",
        mutating_reference,
    )
    with pytest.raises(ValueError) as captured:
        _public(synthetic_case, existing=existing)
    assert str(captured.value) == "INGESTION_RESPONSE_INVARIANT_INVALID"
    assert calls == 1


def test_private_mutation_cannot_modify_caller_existing_input(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_private_response: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = [
        copy.deepcopy(fresh_private_response["new_authority_records"][0])
    ]
    existing_snapshot = copy.deepcopy(existing)
    calls = 0

    def mutating_defensive_copy(**keywords):
        nonlocal calls
        calls += 1
        received = keywords[
            "existing_multi_boundary_authority_records"
        ]
        assert received is not existing
        assert received[0] is not existing[0]
        assert received[0]["reviewed_warhead_atom_ids"] is not (
            existing[0]["reviewed_warhead_atom_ids"]
        )
        received[0]["reviewer_id"] = "__private_mutation__"
        return copy.deepcopy(fresh_private_response)

    monkeypatch.setattr(
        design,
        "_reference_evaluate_covapie_current11_multi_boundary_ingestion_v1",
        mutating_defensive_copy,
    )
    with pytest.raises(ValueError) as captured:
        _public(synthetic_case, existing=existing)
    assert str(captured.value) == "INGESTION_RESPONSE_INVARIANT_INVALID"
    assert calls == 1
    assert existing == existing_snapshot


def test_unexpected_existing_deepcopy_exception_is_normalized(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UnexpectedDeepcopyFailureSequence(
        Sequence[Mapping[str, Any]]
    ):
        def __getitem__(self, index):
            raise IndexError(index)

        def __len__(self) -> int:
            return 0

        def __deepcopy__(self, memo):
            raise RuntimeError("unexpected deepcopy failure")

    calls = 0

    def counted_private(**_keywords):
        nonlocal calls
        calls += 1
        raise AssertionError("private evaluator must not be called")

    monkeypatch.setattr(
        design,
        "_reference_evaluate_covapie_current11_multi_boundary_ingestion_v1",
        counted_private,
    )
    with pytest.raises(ValueError) as captured:
        _public(
            synthetic_case,
            existing=UnexpectedDeepcopyFailureSequence(),
        )
    assert str(captured.value) == "INGESTION_RESPONSE_INVARIANT_INVALID"
    assert isinstance(captured.value.__cause__, RuntimeError)
    assert calls == 0


def test_deceptive_deepcopy_returning_self_is_rejected_before_private_call(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_private_response: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class DeceptiveDeepcopySequence(
        Sequence[Mapping[str, Any]]
    ):
        def __init__(self, records):
            self.records = records

        def __len__(self) -> int:
            return len(self.records)

        def __getitem__(self, index):
            return self.records[index]

        def __deepcopy__(self, memo):
            return self

    records = [
        copy.deepcopy(fresh_private_response["new_authority_records"][0])
    ]
    records_snapshot = copy.deepcopy(records)
    deceptive = DeceptiveDeepcopySequence(records)
    calls = 0

    def counted_private(**_keywords):
        nonlocal calls
        calls += 1
        raise AssertionError("private evaluator must not be called")

    monkeypatch.setattr(
        design,
        "_reference_evaluate_covapie_current11_multi_boundary_ingestion_v1",
        counted_private,
    )
    with pytest.raises(ValueError) as captured:
        _public(synthetic_case, existing=deceptive)
    assert str(captured.value) == "INGESTION_RESPONSE_INVARIANT_INVALID"
    assert calls == 0
    assert records == records_snapshot


def test_checker_enforces_call_budgets_digests_and_zero_writes() -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            str(PYTHON),
            "-B",
            "scripts/check_covapie_current11_multi_boundary_"
            "human_review_ingestion_interface_v1.py",
        ],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    expected_lines = (
        "public_private_fresh_parity=true",
        "response_digest_valid=true",
        "deterministic=true",
        "inputs_unchanged=true",
        "response_isolated=true",
        "private_reference_calls_per_public_evaluation=1",
        "sidecar_builder_calls_per_public_evaluation=1",
        "authority_context_builder_calls_per_public_evaluation=2",
        "compiler_calls_per_public_evaluation=0",
        "adapter_calls_per_public_evaluation=0",
        "predecessor_ingestion_evaluator_calls_per_public_evaluation=0",
        "files_written=false",
        "durable_authority_created=false",
        "v1_authority_modified=false",
        f'interface_response_sha256="{CHECKER._EXPECTED_RESPONSE_SHA256}"',
    )
    assert all(line in completed.stdout for line in expected_lines)
