from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from covalent_ext import (
    covapie_current11_multi_boundary_authority_materialization_and_unified_precedence_design_v1
    as subject,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_contract_design_v1
    as multi_design,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1
    as multi_execution,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_interface_v1
    as public_interface,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_submission_adapter_v1
    as adapter,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_submission_bundle_compiler_v1
    as compiler,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as legacy_design,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as legacy_interface,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_execution_checker(repo_root: Path):
    path = (
        repo_root
        / "scripts/check_covapie_current11_multi_boundary_"
        "human_review_ingestion_execution_bundle_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "multi_execution_checker_for_precedence_tests", path,
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def synthetic_inputs() -> tuple[bytes, bytes, bytes]:
    repo_root = _repo_root()
    checker = _load_execution_checker(repo_root)
    multi_submission, adapter_response, v1_submission, v1_execution = (
        checker._synthetic_case(repo_root)
    )
    multi_execution_payload = (
        multi_execution
        .build_covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1(
            adapter_response_payload=adapter_response,
            source_multi_boundary_submission_bundle=multi_submission,
            source_v1_submission_bundle=v1_submission,
            source_v1_ingestion_execution_bundle=v1_execution,
            repo_root=repo_root,
        )
    )
    return v1_submission, v1_execution, multi_execution_payload


def _evaluate(inputs: tuple[bytes, bytes, bytes]) -> dict[str, Any]:
    return (
        subject
        ._reference_design_covapie_current11_unified_authority_precedence_v1(
            source_v1_submission_bundle=inputs[0],
            source_v1_ingestion_execution_bundle=inputs[1],
            source_multi_boundary_ingestion_execution_bundle=inputs[2],
            repo_root=_repo_root(),
        )
    )


def _ordered_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _rehash_multi(bundle: dict[str, Any], position: int) -> None:
    authority = bundle["new_authority_records"][position]
    result = bundle["ingestion_result_records"][position]
    authority["multi_boundary_authority_record_sha256"] = (
        multi_design._digest(
            authority,
            multi_design.MULTI_BOUNDARY_AUTHORITY_RECORD_FIELDS,
            "multi_boundary_authority_record_sha256",
        )
    )
    result["authority_record_sha256"] = authority[
        "multi_boundary_authority_record_sha256"
    ]
    result["multi_boundary_ingestion_result_sha256"] = multi_design._digest(
        result,
        multi_design.MULTI_BOUNDARY_INGESTION_RESULT_FIELDS,
        "multi_boundary_ingestion_result_sha256",
    )
    response = {
        "multi_boundary_ingestion_interface_response_version":
            bundle["ingestion_interface_response_version"],
        "authority_context_record_sha256":
            bundle["authority_context_record_sha256"],
        "batch_passed": bundle["batch_passed"],
        "ingestion_result_records": tuple(
            bundle["ingestion_result_records"]
        ),
        "new_authority_records": tuple(bundle["new_authority_records"]),
        "multi_boundary_ingestion_interface_response_sha256": "",
    }
    response[
        "multi_boundary_ingestion_interface_response_sha256"
    ] = multi_design._digest(
        response,
        multi_design.MULTI_BOUNDARY_INGESTION_INTERFACE_RESPONSE_FIELDS,
        "multi_boundary_ingestion_interface_response_sha256",
    )
    bundle["ingestion_interface_response_sha256"] = response[
        "multi_boundary_ingestion_interface_response_sha256"
    ]
    bundle["multi_boundary_ingestion_execution_bundle_sha256"] = (
        multi_design._digest(
            bundle,
            multi_execution.EXACT16_FIELDS,
            "multi_boundary_ingestion_execution_bundle_sha256",
        )
    )


def _decoded_validated_executions(
    inputs: tuple[bytes, bytes, bytes],
) -> tuple[dict[str, Any], dict[str, Any]]:
    context = (
        legacy_interface
        .build_current11_warhead_boundary_review_ingestion_authority_context_v1(
            _repo_root()
        )
    )
    legacy = multi_design._decode_v1_execution(
        inputs[1],
        source_v1_submission_bundle=inputs[0],
        expected_authority_context_record_sha256=context.context_record[
            "ingestion_authority_context_record_sha256"
        ],
    )
    multi = json.loads(inputs[2])
    return legacy, multi


def test_private_design_surface_and_frozen_future_actions() -> None:
    assert subject.__all__ == ()
    assert subject._FUTURE_ACTION_NAMES == (
        "implement_covapie_current11_multi_boundary_authority_bundle_v1",
        "implement_covapie_current11_unified_effective_authority_view_v1",
    )
    assert not any(
        hasattr(subject, action) for action in subject._FUTURE_ACTION_NAMES
    )


def test_import_is_silent() -> None:
    module_name = (
        "covalent_ext.covapie_current11_multi_boundary_authority_"
        "materialization_and_unified_precedence_design_v1"
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            (
                "import importlib;"
                f"importlib.import_module({module_name!r})"
            ),
        ],
        cwd=_repo_root(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_exact_response_resolution_and_precedence_profile(
    synthetic_inputs: tuple[bytes, bytes, bytes],
) -> None:
    response = _evaluate(synthetic_inputs)
    records = response["resolution_records"]
    assert tuple(response) == subject._RESPONSE_FIELDS
    assert type(records) is tuple
    assert len(records) == 11
    assert all(tuple(record) == subject._RESOLUTION_FIELDS for record in records)
    assert tuple(record["sample_index_row_id"] for record in records) == (
        subject._EXPECTED_SAMPLES
    )
    assert response["effective_legacy_exact_one_count"] == 6
    assert response["effective_multi_boundary_exact_two_count"] == 5
    assert response[
        "ready_for_authority_and_unified_view_implementation"
    ] is True

    legacy_records = (*records[:5], records[10])
    multi_records = records[5:10]
    assert all(
        record["effective_authority_namespace"]
        == subject._LEGACY_NAMESPACE
        and record["effective_boundary_cardinality"] == 1
        and record["precedence_reason"] == subject._LEGACY_REASON
        and record["multi_boundary_authority_record_sha256"] == ""
        and record["multi_boundary_authority_status"] == ""
        for record in legacy_records
    )
    assert all(
        record["effective_authority_namespace"]
        == subject._MULTI_NAMESPACE
        and record["effective_boundary_cardinality"] == 2
        and record["precedence_reason"] == subject._MULTI_REASON
        and record["legacy_v1_authority_status"] == "quarantined"
        and record["legacy_v1_sample_quarantined"] is True
        and record["multi_boundary_authority_status"] == "active"
        for record in multi_records
    )


def test_record_and_response_digests(
    synthetic_inputs: tuple[bytes, bytes, bytes],
) -> None:
    response = _evaluate(synthetic_inputs)
    for record in response["resolution_records"]:
        assert record[
            "unified_precedence_resolution_record_sha256"
        ] == subject._record_sha256(
            record,
            subject._RESOLUTION_FIELDS,
            "unified_precedence_resolution_record_sha256",
        )
    assert response[
        "unified_authority_precedence_design_response_sha256"
    ] == subject._record_sha256(
        response,
        subject._RESPONSE_FIELDS,
        "unified_authority_precedence_design_response_sha256",
    )


def test_deterministic_inputs_and_source_authorities_unchanged(
    synthetic_inputs: tuple[bytes, bytes, bytes],
) -> None:
    input_snapshots = tuple(bytes(value) for value in synthetic_inputs)
    before = (
        copy.deepcopy(json.loads(synthetic_inputs[1])["new_authority_records"]),
        copy.deepcopy(json.loads(synthetic_inputs[2])["new_authority_records"]),
    )
    first = _evaluate(synthetic_inputs)
    second = _evaluate(synthetic_inputs)
    after = (
        json.loads(synthetic_inputs[1])["new_authority_records"],
        json.loads(synthetic_inputs[2])["new_authority_records"],
    )
    assert first == second
    assert input_snapshots == synthetic_inputs
    assert before == after
    assert all(
        record["source_authorities_unchanged"] is True
        for record in first["resolution_records"]
    )


def test_missing_and_unexpected_multi_authority_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes],
) -> None:
    legacy, multi = _decoded_validated_executions(synthetic_inputs)
    missing = copy.deepcopy(multi)
    missing["new_authority_records"].pop()
    with pytest.raises(ValueError, match="AUTHORITY_NAMESPACE_COVERAGE"):
        subject._build_resolution_records(
            legacy_execution=legacy,
            multi_execution_bundle=missing,
        )

    unexpected = copy.deepcopy(multi)
    unexpected["new_authority_records"][0][
        "sample_index_row_id"
    ] = subject._EXPECTED_SAMPLES[0]
    with pytest.raises(ValueError, match="AUTHORITY_NAMESPACE_COVERAGE"):
        subject._build_resolution_records(
            legacy_execution=legacy,
            multi_execution_bundle=unexpected,
        )


def test_active_active_ambiguity_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes],
) -> None:
    legacy, multi = _decoded_validated_executions(synthetic_inputs)
    authority = legacy["new_authority_records"][5]
    authority["authority_status"] = "active"
    with pytest.raises(ValueError, match="ACTIVE_ACTIVE_AMBIGUITY"):
        subject._build_resolution_records(
            legacy_execution=legacy,
            multi_execution_bundle=multi,
        )


def test_legacy_quarantine_and_multi_active_status_drift_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes],
) -> None:
    legacy, multi = _decoded_validated_executions(synthetic_inputs)
    legacy["new_authority_records"][5]["sample_quarantined"] = False
    with pytest.raises(ValueError, match="LEGACY_V1_QUARANTINE_STATUS_DRIFT"):
        subject._build_resolution_records(
            legacy_execution=legacy,
            multi_execution_bundle=multi,
        )

    legacy, multi = _decoded_validated_executions(synthetic_inputs)
    multi["new_authority_records"][0]["authority_status"] = "quarantined"
    with pytest.raises(ValueError, match="MULTI_AUTHORITY_ACTIVE_STATUS_DRIFT"):
        subject._build_resolution_records(
            legacy_execution=legacy,
            multi_execution_bundle=multi,
        )


def test_same_sample_predecessor_backlink_drift_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes],
) -> None:
    bundle = json.loads(synthetic_inputs[2])
    bundle["new_authority_records"][0][
        "source_v1_quarantine_authority_record_sha256"
    ] = "0" * 64
    _rehash_multi(bundle, 0)
    with pytest.raises(ValueError, match="FRESH_AUTHORITY_LINKAGE"):
        _evaluate((*synthetic_inputs[:2], _ordered_bytes(bundle)))


def test_v1_and_multi_execution_digest_drift_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes],
) -> None:
    legacy = json.loads(synthetic_inputs[1])
    legacy["ingestion_execution_bundle_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="LEGACY_V1_EXECUTION_INVALID"):
        _evaluate((
            synthetic_inputs[0],
            _ordered_bytes(legacy),
            synthetic_inputs[2],
        ))

    multi = json.loads(synthetic_inputs[2])
    multi["multi_boundary_ingestion_execution_bundle_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="LINEAGE_OR_DIGEST"):
        _evaluate((*synthetic_inputs[:2], _ordered_bytes(multi)))


def test_sample_duplicate_or_missing_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes],
) -> None:
    bundle = json.loads(synthetic_inputs[2])
    duplicate_sample = bundle["new_authority_records"][0][
        "sample_index_row_id"
    ]
    bundle["new_authority_records"][1][
        "sample_index_row_id"
    ] = duplicate_sample
    bundle["ingestion_result_records"][1][
        "sample_index_row_id"
    ] = duplicate_sample
    _rehash_multi(bundle, 1)
    with pytest.raises(ValueError, match="SAMPLE_ORDER"):
        _evaluate((*synthetic_inputs[:2], _ordered_bytes(bundle)))


@pytest.mark.parametrize("position", (0, 1, 2))
def test_invalid_exact_byte_type_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes],
    position: int,
) -> None:
    invalid = list(synthetic_inputs)
    invalid[position] = bytearray(invalid[position])  # type: ignore[assignment]
    with pytest.raises(ValueError, match="INPUT_MUST_BE_EXACT_BYTES"):
        _evaluate(tuple(invalid))  # type: ignore[arg-type]


def test_zero_writes_and_forbidden_call_budget(
    synthetic_inputs: tuple[bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {
        "compiler": 0,
        "adapter": 0,
        "public_interface": 0,
        "private_evaluator": 0,
        "writes": 0,
    }

    def forbidden(name: str):
        def fail(*_arguments, **_keywords):
            calls[name] += 1
            raise AssertionError(f"forbidden call: {name}")

        return fail

    monkeypatch.setattr(
        compiler,
        "compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1",
        forbidden("compiler"),
    )
    monkeypatch.setattr(
        adapter,
        "adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1",
        forbidden("adapter"),
    )
    monkeypatch.setattr(
        public_interface,
        "evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1",
        forbidden("public_interface"),
    )
    monkeypatch.setattr(
        multi_design,
        "_reference_evaluate_covapie_current11_multi_boundary_ingestion_v1",
        forbidden("private_evaluator"),
    )
    for method in ("write_bytes", "write_text", "touch", "mkdir"):
        monkeypatch.setattr(Path, method, forbidden("writes"))

    response = _evaluate(synthetic_inputs)
    assert response[
        "ready_for_authority_and_unified_view_implementation"
    ] is True
    assert calls == {
        "compiler": 0,
        "adapter": 0,
        "public_interface": 0,
        "private_evaluator": 0,
        "writes": 0,
    }


def test_internal_helper_does_not_mutate_source_authority_objects(
    synthetic_inputs: tuple[bytes, bytes, bytes],
) -> None:
    legacy, multi = _decoded_validated_executions(synthetic_inputs)
    snapshots = (
        copy.deepcopy(legacy["new_authority_records"]),
        copy.deepcopy(multi["new_authority_records"]),
    )
    subject._build_resolution_records(
        legacy_execution=legacy,
        multi_execution_bundle=multi,
    )
    assert snapshots == (
        legacy["new_authority_records"],
        multi["new_authority_records"],
    )
