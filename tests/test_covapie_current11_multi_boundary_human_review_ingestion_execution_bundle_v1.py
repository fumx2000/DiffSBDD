from __future__ import annotations

import copy
import hashlib
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import get_type_hints

import pytest

from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_contract_design_v1
    as design,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1
    as execution,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_interface_v1
    as public_interface,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as predecessor_ingestion_interface,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(
    "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/"
    "covapie-envs/diffsbdd-legacy-test-v1/bin/python3.10"
)
FUNCTION = (
    execution
    .build_covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1
)
ERROR = "MULTI_BOUNDARY_INGESTION_EXECUTION_RESPONSE_INVALID"
EXPECTED_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(6, 11)
)


def _load_checker():
    import importlib.util

    path = (
        REPO_ROOT
        / "scripts/check_covapie_current11_multi_boundary_"
        "human_review_ingestion_execution_bundle_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "multi_boundary_execution_checker_for_tests", path,
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
def fresh_response(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> dict[str, object]:
    multi_submission, adapter_response, v1_submission, v1_execution = (
        synthetic_case
    )
    return public_interface.evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1(
        adapter_response_payload=adapter_response,
        source_multi_boundary_submission_bundle=multi_submission,
        source_v1_submission_bundle=v1_submission,
        source_v1_ingestion_execution_bundle=v1_execution,
        repo_root=REPO_ROOT,
    )


def _build(case: tuple[bytes, bytes, bytes, bytes]) -> bytes:
    multi_submission, adapter_response, v1_submission, v1_execution = case
    return FUNCTION(
        adapter_response_payload=adapter_response,
        source_multi_boundary_submission_bundle=multi_submission,
        source_v1_submission_bundle=v1_submission,
        source_v1_ingestion_execution_bundle=v1_execution,
        repo_root=REPO_ROOT,
    )


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_sha(
    record: dict[str, object],
    fields: tuple[str, ...],
    excluded: str,
) -> str:
    return _sha256(json.dumps(
        {field: record[field] for field in fields if field != excluded},
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8"))


def _rehash_response(response: dict[str, object]) -> None:
    response["multi_boundary_ingestion_interface_response_sha256"] = (
        _canonical_sha(
            response,
            design.MULTI_BOUNDARY_INGESTION_INTERFACE_RESPONSE_FIELDS,
            "multi_boundary_ingestion_interface_response_sha256",
        )
    )


def _rehash_result(result: dict[str, object]) -> None:
    result["multi_boundary_ingestion_result_sha256"] = _canonical_sha(
        result,
        design.MULTI_BOUNDARY_INGESTION_RESULT_FIELDS,
        "multi_boundary_ingestion_result_sha256",
    )


def _rehash_authority(authority: dict[str, object]) -> None:
    authority["multi_boundary_authority_record_sha256"] = _canonical_sha(
        authority,
        design.MULTI_BOUNDARY_AUTHORITY_RECORD_FIELDS,
        "multi_boundary_authority_record_sha256",
    )


def _patched_response(monkeypatch: pytest.MonkeyPatch, response: object) -> None:
    def evaluate(**_keywords):
        return copy.deepcopy(response)

    monkeypatch.setattr(
        public_interface,
        "evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1",
        evaluate,
    )


def test_public_api_signature_annotations_and_all() -> None:
    assert execution.__all__ == (
        "build_covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1",
    )
    signature = inspect.signature(FUNCTION)
    assert tuple(signature.parameters) == (
        "adapter_response_payload",
        "source_multi_boundary_submission_bundle",
        "source_v1_submission_bundle",
        "source_v1_ingestion_execution_bundle",
        "repo_root",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert get_type_hints(FUNCTION) == {
        "adapter_response_payload": bytes,
        "source_multi_boundary_submission_bundle": bytes,
        "source_v1_submission_bundle": bytes,
        "source_v1_ingestion_execution_bundle": bytes,
        "repo_root": Path,
        "return": bytes,
    }


def test_constants_exact16_and_public_interface_source_sha() -> None:
    assert execution.EXECUTION_BUNDLE_VERSION == (
        "covapie_current11_multi_boundary_human_review_"
        "ingestion_execution_bundle_v1"
    )
    assert execution.PUBLIC_INTERFACE_COMMIT == (
        "653bacfb31e69ccfd37f29dcffd77116c9305370"
    )
    assert execution.PUBLIC_INTERFACE_PRODUCTION_SHA256 == (
        "f17a33e52ede082e5a28f20b8a70e4b3d40ca30b69823b4050b2104a3545b0d5"
    )
    assert execution.EXACT16_FIELDS == (
        "multi_boundary_ingestion_execution_bundle_version",
        "source_v1_submission_bundle_sha256",
        "source_v1_ingestion_execution_bundle_filesystem_sha256",
        "source_v1_ingestion_execution_bundle_sha256",
        "source_multi_boundary_submission_bundle_filesystem_sha256",
        "source_multi_boundary_submission_bundle_sha256",
        "source_adapter_response_filesystem_sha256",
        "source_adapter_response_sha256",
        "submission_batch_id",
        "ingestion_interface_response_version",
        "authority_context_record_sha256",
        "batch_passed",
        "ingestion_result_records",
        "new_authority_records",
        "ingestion_interface_response_sha256",
        "multi_boundary_ingestion_execution_bundle_sha256",
    )
    source = (
        REPO_ROOT
        / "src/covalent_ext/covapie_current11_multi_boundary_"
        "human_review_ingestion_interface_v1.py"
    ).read_bytes()
    assert _sha256(source) == execution.PUBLIC_INTERFACE_PRODUCTION_SHA256


def test_import_is_silent() -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            str(PYTHON),
            "-B",
            "-c",
            "from covalent_ext import "
            "covapie_current11_multi_boundary_human_review_"
            "ingestion_execution_bundle_v1",
        ],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_success_exact16_deterministic_transport_and_round_trip(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    first = _build(synthetic_case)
    second = _build(synthetic_case)
    assert type(first) is bytes
    assert first == second
    assert first
    assert len(first) < 1024 * 1024
    assert not first.startswith(b"\xef\xbb\xbf")
    assert b"\x00" not in first
    assert b"\n" not in first
    assert not first.endswith((b"\n", b"\r"))
    _, bundle = design._strict_json_object(first)
    assert tuple(bundle) == execution.EXACT16_FIELDS
    assert bundle["multi_boundary_ingestion_execution_bundle_version"] == (
        execution.EXECUTION_BUNDLE_VERSION
    )
    assert json.dumps(
        bundle,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8") == first


def test_execution_internal_digest(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    bundle = json.loads(_build(synthetic_case))
    assert bundle["multi_boundary_ingestion_execution_bundle_sha256"] == (
        _canonical_sha(
            bundle,
            execution.EXACT16_FIELDS,
            "multi_boundary_ingestion_execution_bundle_sha256",
        )
    )


def test_source_filesystem_and_internal_sha_lineage(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    multi_submission, adapter_response, v1_submission, v1_execution = (
        synthetic_case
    )
    bundle = json.loads(_build(synthetic_case))
    multi = json.loads(multi_submission)
    adapter = json.loads(adapter_response)
    predecessor = json.loads(v1_execution)
    assert bundle["source_v1_submission_bundle_sha256"] == _sha256(
        v1_submission
    )
    assert bundle[
        "source_v1_ingestion_execution_bundle_filesystem_sha256"
    ] == _sha256(v1_execution)
    assert bundle["source_v1_ingestion_execution_bundle_sha256"] == (
        predecessor["ingestion_execution_bundle_sha256"]
    )
    assert bundle[
        "source_multi_boundary_submission_bundle_filesystem_sha256"
    ] == _sha256(multi_submission)
    assert bundle["source_multi_boundary_submission_bundle_sha256"] == (
        multi["multi_boundary_submission_bundle_sha256"]
    )
    assert bundle["source_adapter_response_filesystem_sha256"] == _sha256(
        adapter_response
    )
    assert bundle["source_adapter_response_sha256"] == (
        adapter["multi_boundary_submission_adapter_response_sha256"]
    )


def test_reconstructed_exact6_response_digest_and_nested_validation(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    bundle = json.loads(_build(synthetic_case))
    response = {
        "multi_boundary_ingestion_interface_response_version":
            bundle["ingestion_interface_response_version"],
        "authority_context_record_sha256":
            bundle["authority_context_record_sha256"],
        "batch_passed": bundle["batch_passed"],
        "ingestion_result_records":
            tuple(bundle["ingestion_result_records"]),
        "new_authority_records": tuple(bundle["new_authority_records"]),
        "multi_boundary_ingestion_interface_response_sha256":
            bundle["ingestion_interface_response_sha256"],
    }
    assert tuple(response) == (
        design.MULTI_BOUNDARY_INGESTION_INTERFACE_RESPONSE_FIELDS
    )
    design._validate_interface_response(response)
    assert response[
        "multi_boundary_ingestion_interface_response_sha256"
    ] == _canonical_sha(
        response,
        design.MULTI_BOUNDARY_INGESTION_INTERFACE_RESPONSE_FIELDS,
        "multi_boundary_ingestion_interface_response_sha256",
    )
    for result in response["ingestion_result_records"]:
        assert tuple(result) == design.MULTI_BOUNDARY_INGESTION_RESULT_FIELDS
        design._validate_result_record(result)
    for authority in response["new_authority_records"]:
        assert tuple(authority) == design.MULTI_BOUNDARY_AUTHORITY_RECORD_FIELDS
        design._validate_authority_record(authority)


def test_fresh_sample_order_decision_profile_and_authority_effect(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    bundle = json.loads(_build(synthetic_case))
    results = bundle["ingestion_result_records"]
    authorities = bundle["new_authority_records"]
    assert tuple(result["sample_index_row_id"] for result in results) == (
        EXPECTED_SAMPLES
    )
    assert tuple(
        authority["sample_index_row_id"] for authority in authorities
    ) == EXPECTED_SAMPLES
    decisions = [
        authority["review_decision"] for authority in authorities
    ]
    assert decisions.count("accept_verified_two_boundary_proposal") == 4
    assert decisions.count(
        "revise_two_boundary_atom_set_and_boundaries"
    ) == 1
    assert decisions.count("quarantine") == 0
    assert all(
        authority["authority_status"] == "active"
        and authority["sample_quarantined"] is False
        and authority[
            "complete_warhead_atom_set_authority_available"
        ] is True
        and authority[
            "exact_two_attachment_boundaries_authority_available"
        ] is True
        and authority["v1_quarantine_authority_unchanged"] is True
        for authority in authorities
    )


def test_result_authority_position_linkage_and_unique_authority_sha(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    bundle = json.loads(_build(synthetic_case))
    authorities = bundle["new_authority_records"]
    for result, authority in zip(
        bundle["ingestion_result_records"], authorities
    ):
        assert result["sample_index_row_id"] == authority[
            "sample_index_row_id"
        ]
        assert result[
            "source_multi_boundary_review_record_sha256"
        ] == authority["source_multi_boundary_review_record_sha256"]
        assert result["source_ingestion_envelope_sha256"] == authority[
            "source_ingestion_envelope_sha256"
        ]
        assert result["review_decision"] == authority["review_decision"]
        assert result["authority_disposition"] == authority[
            "authority_disposition"
        ]
        assert result["authority_record_sha256"] == authority[
            "multi_boundary_authority_record_sha256"
        ]
    assert len({
        authority["multi_boundary_authority_record_sha256"]
        for authority in authorities
    }) == 5


def test_embedded_current_source_lineage_substitution_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, object],
) -> None:
    substituted = copy.deepcopy(fresh_response)
    for result, authority in zip(
        substituted["ingestion_result_records"],
        substituted["new_authority_records"],
    ):
        authority[
            "source_multi_boundary_submission_bundle_sha256"
        ] = "1" * 64
        authority[
            "source_multi_boundary_submission_adapter_response_sha256"
        ] = "2" * 64
        _rehash_authority(authority)
        result["authority_record_sha256"] = authority[
            "multi_boundary_authority_record_sha256"
        ]
        _rehash_result(result)
    _rehash_response(substituted)
    design._validate_interface_response(substituted)

    _patched_response(monkeypatch, substituted)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_case)


def test_embedded_v1_authority_lineage_substitution_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, object],
) -> None:
    substituted = copy.deepcopy(fresh_response)
    result = substituted["ingestion_result_records"][0]
    authority = substituted["new_authority_records"][0]
    authority[
        "source_v1_quarantine_authority_record_sha256"
    ] = "3" * 64
    authority["source_v1_review_record_sha256"] = "4" * 64
    _rehash_authority(authority)
    result["authority_record_sha256"] = authority[
        "multi_boundary_authority_record_sha256"
    ]
    _rehash_result(result)
    _rehash_response(substituted)
    design._validate_interface_response(substituted)

    _patched_response(monkeypatch, substituted)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_case)


def test_four_inputs_remain_byte_identical(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    snapshots = tuple(bytes(payload) for payload in synthetic_case)
    _build(synthetic_case)
    assert synthetic_case == snapshots


def test_public_interface_is_called_once_with_only_fresh_arguments(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    original = (
        public_interface
        .evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1
    )
    observed: list[dict[str, object]] = []

    def counted(**keywords):
        observed.append(keywords)
        return original(**keywords)

    monkeypatch.setattr(
        public_interface,
        "evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1",
        counted,
    )
    _build(synthetic_case)
    assert len(observed) == 1
    assert tuple(observed[0]) == (
        "adapter_response_payload",
        "source_multi_boundary_submission_bundle",
        "source_v1_submission_bundle",
        "source_v1_ingestion_execution_bundle",
        "repo_root",
    )
    assert "existing_multi_boundary_authority_records" not in observed[0]


def test_checker_confirms_full_call_budget_and_no_writes() -> None:
    assertions = CHECKER._check(REPO_ROOT)
    assert assertions["public_interface_calls_per_build"] == 1
    assert assertions["private_reference_calls_per_build"] == 1
    assert assertions["sidecar_builder_calls_per_build"] == 1
    assert assertions["authority_context_builder_calls_per_build"] == 3
    assert assertions["compiler_calls_per_build"] == 0
    assert assertions["adapter_calls_per_build"] == 0
    assert (
        assertions["predecessor_ingestion_evaluator_calls_per_build"] == 0
    )
    assert assertions["files_written"] is False
    assert assertions["durable_execution_file_created"] is False
    assert assertions["durable_authority_created"] is False
    assert assertions["v1_authority_modified"] is False


def test_production_does_not_name_private_evaluator_or_forbidden_calls() -> None:
    source = inspect.getsource(execution)
    assert (
        "_reference_evaluate_covapie_current11_multi_boundary_ingestion_v1"
        not in source
    )
    assert (
        "compile_covapie_current11_multi_boundary_human_review_"
        "submission_bundle_v1" not in source
    )
    assert (
        "adapt_covapie_current11_multi_boundary_human_review_"
        "submission_bundle_v1" not in source
    )
    assert (
        "evaluate_current11_warhead_boundary_review_ingestion_v1"
        not in source
    )


def test_failed_replay_and_conflict_responses_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, object],
) -> None:
    failed = design._empty_failure_response("ADAPTER_RESPONSE_INVALID")
    existing = copy.deepcopy(fresh_response["new_authority_records"])
    replay = (
        public_interface
        .evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1(
            adapter_response_payload=synthetic_case[1],
            source_multi_boundary_submission_bundle=synthetic_case[0],
            source_v1_submission_bundle=synthetic_case[2],
            source_v1_ingestion_execution_bundle=synthetic_case[3],
            repo_root=REPO_ROOT,
            existing_multi_boundary_authority_records=existing,
        )
    )
    conflicting_existing = copy.deepcopy(existing)
    conflicting_existing[0]["reviewer_id"] = "different_reviewer"
    _rehash_authority(conflicting_existing[0])
    conflict = (
        public_interface
        .evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1(
            adapter_response_payload=synthetic_case[1],
            source_multi_boundary_submission_bundle=synthetic_case[0],
            source_v1_submission_bundle=synthetic_case[2],
            source_v1_ingestion_execution_bundle=synthetic_case[3],
            repo_root=REPO_ROOT,
            existing_multi_boundary_authority_records=conflicting_existing,
        )
    )
    assert replay["batch_passed"] is True
    assert replay["new_authority_records"] == ()
    assert conflict["batch_passed"] is False
    for response in (failed, replay, conflict):
        _patched_response(monkeypatch, response)
        with pytest.raises(ValueError, match=f"^{ERROR}$"):
            _build(synthetic_case)


def test_mixed_replay_response_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, object],
) -> None:
    mixed = (
        public_interface
        .evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1(
            adapter_response_payload=synthetic_case[1],
            source_multi_boundary_submission_bundle=synthetic_case[0],
            source_v1_submission_bundle=synthetic_case[2],
            source_v1_ingestion_execution_bundle=synthetic_case[3],
            repo_root=REPO_ROOT,
            existing_multi_boundary_authority_records=(
                fresh_response["new_authority_records"][0],
            ),
        )
    )
    assert mixed["batch_passed"] is True
    assert len(mixed["new_authority_records"]) == 4
    _patched_response(monkeypatch, mixed)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_case)


def test_malformed_exact6_and_wrong_response_type_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, object],
) -> None:
    malformed = copy.deepcopy(fresh_response)
    del malformed["batch_passed"]
    for response in (malformed, []):
        _patched_response(monkeypatch, response)
        with pytest.raises(ValueError, match=f"^{ERROR}$"):
            _build(synthetic_case)


def test_malformed_nested_result_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, object],
) -> None:
    malformed = copy.deepcopy(fresh_response)
    malformed["ingestion_result_records"][0]["passed"] = False
    _patched_response(monkeypatch, malformed)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_case)


def test_malformed_nested_authority_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, object],
) -> None:
    malformed = copy.deepcopy(fresh_response)
    malformed["new_authority_records"][0]["authority_status"] = "quarantined"
    _patched_response(monkeypatch, malformed)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_case)


def test_wrong_sample_order_is_rejected_after_valid_response_digest(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, object],
) -> None:
    wrong_order = copy.deepcopy(fresh_response)
    wrong_order["ingestion_result_records"] = tuple(reversed(
        wrong_order["ingestion_result_records"]
    ))
    wrong_order["new_authority_records"] = tuple(reversed(
        wrong_order["new_authority_records"]
    ))
    _rehash_response(wrong_order)
    design._validate_interface_response(wrong_order)
    _patched_response(monkeypatch, wrong_order)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_case)


def test_wrong_decision_profile_is_rejected_after_nested_rehash(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, object],
) -> None:
    wrong_profile = copy.deepcopy(fresh_response)
    result = wrong_profile["ingestion_result_records"][0]
    authority = wrong_profile["new_authority_records"][0]
    assert authority["review_decision"] == (
        "accept_verified_two_boundary_proposal"
    )
    authority["review_decision"] = (
        "revise_two_boundary_atom_set_and_boundaries"
    )
    _rehash_authority(authority)
    result["review_decision"] = authority["review_decision"]
    result["authority_record_sha256"] = authority[
        "multi_boundary_authority_record_sha256"
    ]
    _rehash_result(result)
    _rehash_response(wrong_profile)
    design._validate_interface_response(wrong_profile)
    _patched_response(monkeypatch, wrong_profile)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_case)


def test_valid_quarantine_authority_response_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, object],
) -> None:
    quarantined = copy.deepcopy(fresh_response)
    result = quarantined["ingestion_result_records"][0]
    authority = quarantined["new_authority_records"][0]
    authority["review_decision"] = "quarantine"
    authority["reviewed_warhead_atom_ids"] = []
    authority["reviewed_boundary_records"] = []
    authority["authority_disposition"] = (
        "reviewed_multi_boundary_quarantine_recorded"
    )
    authority["complete_warhead_atom_set_authority_available"] = False
    authority["exact_two_attachment_boundaries_authority_available"] = False
    authority["sample_quarantined"] = True
    authority["authority_status"] = "quarantined"
    _rehash_authority(authority)
    result["review_decision"] = "quarantine"
    result["authority_disposition"] = authority["authority_disposition"]
    result["authority_record_sha256"] = authority[
        "multi_boundary_authority_record_sha256"
    ]
    _rehash_result(result)
    _rehash_response(quarantined)
    design._validate_interface_response(quarantined)
    _patched_response(monkeypatch, quarantined)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_case)


def test_strict_source_json_and_internal_digests_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, object],
) -> None:
    multi = json.loads(synthetic_case[0])
    multi["multi_boundary_submission_bundle_sha256"] = "0" * 64
    bad_multi_digest = json.dumps(
        multi, ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")
    adapter = json.loads(synthetic_case[1])
    adapter[
        "multi_boundary_submission_adapter_response_sha256"
    ] = "0" * 64
    bad_adapter_digest = json.dumps(
        adapter, ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")
    predecessor = json.loads(synthetic_case[3])
    predecessor["ingestion_execution_bundle_sha256"] = "0" * 64
    bad_predecessor_digest = json.dumps(
        predecessor, ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")
    cases = (
        (
            synthetic_case[0] + b"\n",
            synthetic_case[1],
            synthetic_case[2],
            synthetic_case[3],
        ),
        (
            synthetic_case[0],
            b'{"duplicate":1,"duplicate":2}',
            synthetic_case[2],
            synthetic_case[3],
        ),
        (
            bad_multi_digest,
            synthetic_case[1],
            synthetic_case[2],
            synthetic_case[3],
        ),
        (
            synthetic_case[0],
            bad_adapter_digest,
            synthetic_case[2],
            synthetic_case[3],
        ),
        (
            synthetic_case[0],
            synthetic_case[1],
            synthetic_case[2] + b"\n",
            synthetic_case[3],
        ),
        (
            synthetic_case[0],
            synthetic_case[1],
            synthetic_case[2],
            bad_predecessor_digest,
        ),
    )
    _patched_response(monkeypatch, fresh_response)
    for case in cases:
        with pytest.raises(ValueError, match=f"^{ERROR}$"):
            _build(case)


def test_predecessor_authority_context_substitution_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, object],
) -> None:
    predecessor = json.loads(synthetic_case[3])
    original_context_sha256 = predecessor[
        "authority_context_record_sha256"
    ]
    predecessor["authority_context_record_sha256"] = "0" * 64
    predecessor_response = {
        "interface_response_version":
            predecessor["ingestion_interface_response_version"],
        "authority_context_record_sha256":
            predecessor["authority_context_record_sha256"],
        "batch_passed": predecessor["batch_passed"],
        "ingestion_result_records":
            predecessor["ingestion_result_records"],
        "new_authority_records": predecessor["new_authority_records"],
        "interface_response_sha256": "",
    }
    predecessor_response["interface_response_sha256"] = (
        predecessor_ingestion_interface.interface_response_sha256(
            predecessor_response
        )
    )
    predecessor["ingestion_interface_response_sha256"] = (
        predecessor_response["interface_response_sha256"]
    )
    predecessor["ingestion_execution_bundle_sha256"] = _canonical_sha(
        predecessor,
        tuple(predecessor),
        "ingestion_execution_bundle_sha256",
    )
    substituted_predecessor_payload = json.dumps(
        predecessor,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")

    assert predecessor["authority_context_record_sha256"] != (
        original_context_sha256
    )
    assert predecessor_response["interface_response_sha256"] == (
        predecessor_ingestion_interface.interface_response_sha256(
            predecessor_response
        )
    )
    assert predecessor["ingestion_execution_bundle_sha256"] == (
        _canonical_sha(
            predecessor,
            tuple(predecessor),
            "ingestion_execution_bundle_sha256",
        )
    )
    self_expected_predecessor = design._decode_v1_execution(
        substituted_predecessor_payload,
        source_v1_submission_bundle=synthetic_case[2],
        expected_authority_context_record_sha256="0" * 64,
    )
    assert self_expected_predecessor[
        "authority_context_record_sha256"
    ] == "0" * 64

    # Refresh the downstream exact-byte lineage so no filesystem or internal
    # source-digest mismatch can be the reason the builder rejects.
    multi_submission = json.loads(synthetic_case[0])
    multi_submission[
        "source_ingestion_execution_bundle_filesystem_sha256"
    ] = _sha256(substituted_predecessor_payload)
    multi_submission["source_ingestion_execution_bundle_sha256"] = (
        predecessor["ingestion_execution_bundle_sha256"]
    )
    multi_submission["multi_boundary_submission_bundle_sha256"] = (
        _canonical_sha(
            multi_submission,
            tuple(multi_submission),
            "multi_boundary_submission_bundle_sha256",
        )
    )
    substituted_multi_submission_payload = json.dumps(
        multi_submission,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")

    adapter_response = json.loads(synthetic_case[1])
    adapter_response["source_payload_sha256"] = _sha256(
        substituted_multi_submission_payload
    )
    adapter_response["canonical_source_bundle_sha256"] = (
        multi_submission["multi_boundary_submission_bundle_sha256"]
    )
    for result, envelope in zip(
        adapter_response["adapter_result_records"],
        adapter_response["adapted_submissions"],
    ):
        envelope[
            "source_multi_boundary_submission_bundle_sha256"
        ] = multi_submission["multi_boundary_submission_bundle_sha256"]
        envelope["multi_boundary_ingestion_envelope_sha256"] = (
            _canonical_sha(
                envelope,
                tuple(envelope),
                "multi_boundary_ingestion_envelope_sha256",
            )
        )
        result["ingestion_envelope_sha256"] = envelope[
            "multi_boundary_ingestion_envelope_sha256"
        ]
        result["multi_boundary_submission_adapter_result_sha256"] = (
            _canonical_sha(
                result,
                tuple(result),
                "multi_boundary_submission_adapter_result_sha256",
            )
        )
    adapter_response[
        "multi_boundary_submission_adapter_response_sha256"
    ] = _canonical_sha(
        adapter_response,
        tuple(adapter_response),
        "multi_boundary_submission_adapter_response_sha256",
    )
    substituted_adapter_response_payload = json.dumps(
        adapter_response,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")

    validated_multi_submission = (
        design._validate_multi_boundary_submission(
            substituted_multi_submission_payload
        )
    )
    design._validate_adapter_response(
        substituted_adapter_response_payload,
        source_payload=substituted_multi_submission_payload,
        source_bundle=validated_multi_submission,
    )
    _patched_response(monkeypatch, fresh_response)
    substituted_case = (
        substituted_multi_submission_payload,
        substituted_adapter_response_payload,
        synthetic_case[2],
        substituted_predecessor_payload,
    )
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(substituted_case)


@pytest.mark.parametrize(
    ("position", "invalid"),
    (
        (0, bytearray()),
        (1, memoryview(b"{}")),
        (2, "{}"),
        (3, None),
    ),
)
def test_exact_bytes_are_required(
    position: int,
    invalid: object,
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    case = list(synthetic_case)
    case[position] = invalid
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(tuple(case))


def test_exact_path_type_is_required(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        FUNCTION(
            adapter_response_payload=synthetic_case[1],
            source_multi_boundary_submission_bundle=synthetic_case[0],
            source_v1_submission_bundle=synthetic_case[2],
            source_v1_ingestion_execution_bundle=synthetic_case[3],
            repo_root=str(REPO_ROOT),
        )


def test_canonical_serialization_exception_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    def fail(_value: object) -> bytes:
        raise RuntimeError("serialization probe")

    monkeypatch.setattr(execution, "_canonical_json_bytes", fail)
    with pytest.raises(ValueError, match=f"^{ERROR}$") as captured:
        _build(synthetic_case)
    assert isinstance(captured.value.__cause__, RuntimeError)
