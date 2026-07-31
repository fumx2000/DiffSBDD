from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from covalent_ext import (
    covapie_current11_multi_boundary_authority_bundle_v1 as subject,
)
from covalent_ext import (
    covapie_current11_multi_boundary_authority_materialization_and_unified_precedence_design_v1
    as precedence_design,
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


REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FUNCTION = (
    subject.build_covapie_current11_multi_boundary_authority_bundle_v1
)
ERROR = "CURRENT11_MULTI_BOUNDARY_AUTHORITY_BUNDLE_INVALID"


def _load_precedence_checker():
    path = (
        REPO_ROOT
        / "scripts/check_covapie_current11_multi_boundary_authority_"
        "materialization_and_unified_precedence_design_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "precedence_checker_for_authority_bundle_tests", path,
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def synthetic_inputs() -> tuple[bytes, bytes, bytes]:
    return _load_precedence_checker()._synthetic_inputs(REPO_ROOT)


def _build(inputs: tuple[bytes, bytes, bytes]) -> bytes:
    return PUBLIC_FUNCTION(
        source_v1_submission_bundle=inputs[0],
        source_v1_ingestion_execution_bundle=inputs[1],
        source_multi_boundary_ingestion_execution_bundle=inputs[2],
        repo_root=REPO_ROOT,
    )


def _ordered_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _design_response(
    inputs: tuple[bytes, bytes, bytes],
) -> dict[str, Any]:
    return (
        precedence_design
        ._reference_design_covapie_current11_unified_authority_precedence_v1(
            source_v1_submission_bundle=inputs[0],
            source_v1_ingestion_execution_bundle=inputs[1],
            source_multi_boundary_ingestion_execution_bundle=inputs[2],
            repo_root=REPO_ROOT,
        )
    )


def _rehash_resolution_and_response(
    response: dict[str, Any],
    position: int | None = None,
) -> None:
    if position is not None:
        record = response["resolution_records"][position]
        record[
            "unified_precedence_resolution_record_sha256"
        ] = subject._record_sha256(
            record,
            precedence_design._RESOLUTION_FIELDS,
            "unified_precedence_resolution_record_sha256",
        )
    response[
        "unified_authority_precedence_design_response_sha256"
    ] = subject._record_sha256(
        response,
        precedence_design._RESPONSE_FIELDS,
        "unified_authority_precedence_design_response_sha256",
    )


def _mock_design(
    monkeypatch: pytest.MonkeyPatch,
    response: dict[str, Any],
) -> None:
    monkeypatch.setattr(
        precedence_design,
        "_reference_design_covapie_current11_unified_authority_precedence_v1",
        lambda **_keywords: copy.deepcopy(response),
    )


def _rehash_execution(execution: dict[str, Any]) -> bytes:
    execution[
        "multi_boundary_ingestion_execution_bundle_sha256"
    ] = subject._record_sha256(
        execution,
        multi_execution.EXACT16_FIELDS,
        "multi_boundary_ingestion_execution_bundle_sha256",
    )
    return _ordered_bytes(execution)


def test_public_api_signature_annotations_constants_and_design_sha() -> None:
    assert subject.__all__ == (
        "build_covapie_current11_multi_boundary_authority_bundle_v1",
    )
    assert subject.AUTHORITY_BUNDLE_VERSION == (
        "covapie_current11_multi_boundary_authority_bundle_v1"
    )
    assert subject.AUTHORITY_NAMESPACE == (
        "exact_two_boundaries_multi_boundary_v1"
    )
    assert subject.PRECEDENCE_DESIGN_COMMIT == (
        "00c2471ca4fc855985989aea7f948ebbfa1b06f4"
    )
    assert subject.PRECEDENCE_DESIGN_PRODUCTION_SHA256 == (
        "17ebcc1c9ca796fb6c7cdf8af0cccc0a96a6ba419760eccb6d4f85fb163e522c"
    )
    design_path = (
        REPO_ROOT
        / "src/covalent_ext/covapie_current11_multi_boundary_authority_"
        "materialization_and_unified_precedence_design_v1.py"
    )
    assert hashlib.sha256(design_path.read_bytes()).hexdigest() == (
        subject.PRECEDENCE_DESIGN_PRODUCTION_SHA256
    )

    signature = inspect.signature(PUBLIC_FUNCTION)
    assert tuple(signature.parameters) == (
        "source_v1_submission_bundle",
        "source_v1_ingestion_execution_bundle",
        "source_multi_boundary_ingestion_execution_bundle",
        "repo_root",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        and parameter.default is inspect.Parameter.empty
        for parameter in signature.parameters.values()
    )
    hints = get_type_hints(PUBLIC_FUNCTION)
    assert hints == {
        "source_v1_submission_bundle": bytes,
        "source_v1_ingestion_execution_bundle": bytes,
        "source_multi_boundary_ingestion_execution_bundle": bytes,
        "repo_root": Path,
        "return": bytes,
    }


def test_import_is_silent() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            (
                "import importlib;"
                "importlib.import_module("
                "'covalent_ext.covapie_current11_multi_boundary_"
                "authority_bundle_v1')"
            ),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_exact16_determinism_lineage_digest_and_transport(
    synthetic_inputs: tuple[bytes, bytes, bytes],
) -> None:
    snapshots = tuple(bytes(value) for value in synthetic_inputs)
    source_execution = json.loads(synthetic_inputs[2])
    source_authorities = source_execution["new_authority_records"]
    source_authority_snapshot = copy.deepcopy(source_authorities)

    first = _build(synthetic_inputs)
    second = _build(synthetic_inputs)
    assert type(first) is bytes
    assert first == second
    assert first and len(first) < 1024 * 1024
    assert not first.startswith(b"\xef\xbb\xbf")
    assert b"\x00" not in first
    assert b"\n" not in first
    bundle = json.loads(first)
    assert tuple(bundle) == subject.EXACT16_FIELDS
    assert bundle["multi_boundary_authority_bundle_version"] == (
        subject.AUTHORITY_BUNDLE_VERSION
    )
    assert bundle["authority_namespace"] == subject.AUTHORITY_NAMESPACE
    assert bundle[
        "source_v1_ingestion_execution_bundle_filesystem_sha256"
    ] == hashlib.sha256(synthetic_inputs[1]).hexdigest()
    assert bundle[
        "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256"
    ] == hashlib.sha256(synthetic_inputs[2]).hexdigest()
    assert bundle["source_multi_boundary_ingestion_execution_bundle_sha256"] == (
        source_execution[
            "multi_boundary_ingestion_execution_bundle_sha256"
        ]
    )
    assert bundle[
        "multi_boundary_authority_bundle_sha256"
    ] == subject._record_sha256(
        bundle,
        subject.EXACT16_FIELDS,
        "multi_boundary_authority_bundle_sha256",
    )
    _, strict_round_trip = multi_design._strict_json_object(first)
    assert strict_round_trip == bundle
    assert tuple(strict_round_trip) == subject.EXACT16_FIELDS
    assert snapshots == synthetic_inputs
    assert source_authority_snapshot == source_authorities

    bundle["authority_records"][0]["reviewed_warhead_atom_ids"].append(
        "MUTATION"
    )
    assert source_authority_snapshot == source_authorities
    assert _build(synthetic_inputs) == first


def test_selected_resolutions_authorities_profile_and_linkage(
    synthetic_inputs: tuple[bytes, bytes, bytes],
) -> None:
    response = _design_response(synthetic_inputs)
    selected = tuple(
        record for record in response["resolution_records"]
        if record["effective_authority_namespace"]
        == subject.AUTHORITY_NAMESPACE
    )
    bundle = json.loads(_build(synthetic_inputs))
    authorities = bundle["authority_records"]
    assert bundle["sample_order"] == list(subject._EXPECTED_SAMPLES)
    assert bundle["selected_resolution_record_sha256s"] == [
        record["unified_precedence_resolution_record_sha256"]
        for record in selected
    ]
    assert len(set(bundle["selected_resolution_record_sha256s"])) == 5
    assert len(authorities) == 5
    assert all(
        tuple(authority)
        == multi_design.MULTI_BOUNDARY_AUTHORITY_RECORD_FIELDS
        for authority in authorities
    )
    for authority in authorities:
        multi_design._validate_authority_record(authority)
    assert len({
        authority["multi_boundary_authority_record_sha256"]
        for authority in authorities
    }) == 5
    assert [authority["review_decision"] for authority in authorities].count(
        "accept_verified_two_boundary_proposal"
    ) == 4
    assert [authority["review_decision"] for authority in authorities].count(
        "revise_two_boundary_atom_set_and_boundaries"
    ) == 1
    assert all(
        resolution["sample_index_row_id"]
        == authority["sample_index_row_id"]
        and resolution["multi_boundary_authority_record_sha256"]
        == authority["multi_boundary_authority_record_sha256"]
        and resolution["effective_authority_record_sha256"]
        == authority["multi_boundary_authority_record_sha256"]
        and resolution["multi_boundary_authority_status"]
        == authority["authority_status"] == "active"
        and resolution["effective_boundary_cardinality"] == 2
        for resolution, authority in zip(selected, authorities)
    )
    assert (
        bundle["authority_record_count"],
        bundle["active_authority_count"],
        bundle["exact_two_boundary_authority_count"],
        bundle["v1_quarantine_backlink_count"],
    ) == (5, 5, 5, 5)


def test_precedence_design_called_exactly_once_and_digest_checked(
    synthetic_inputs: tuple[bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = (
        precedence_design
        ._reference_design_covapie_current11_unified_authority_precedence_v1
    )
    calls = 0

    def counted(**keywords):
        nonlocal calls
        calls += 1
        return original(**keywords)

    monkeypatch.setattr(
        precedence_design,
        "_reference_design_covapie_current11_unified_authority_precedence_v1",
        counted,
    )
    _build(synthetic_inputs)
    assert calls == 1

    response = _design_response(synthetic_inputs)
    response[
        "unified_authority_precedence_design_response_sha256"
    ] = "0" * 64
    _mock_design(monkeypatch, response)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_inputs)


def test_missing_selected_and_unexpected_legacy_resolution_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing = copy.deepcopy(_design_response(synthetic_inputs))
    missing_record = missing["resolution_records"][5]
    missing_record["effective_authority_namespace"] = (
        precedence_design._LEGACY_NAMESPACE
    )
    _rehash_resolution_and_response(missing, 5)
    _mock_design(monkeypatch, missing)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_inputs)

    unexpected = copy.deepcopy(_design_response(synthetic_inputs))
    legacy_record = unexpected["resolution_records"][0]
    legacy_record["effective_authority_namespace"] = (
        subject.AUTHORITY_NAMESPACE
    )
    _rehash_resolution_and_response(unexpected, 0)
    _mock_design(monkeypatch, unexpected)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_inputs)


def test_resolution_effective_sha_and_boundary_cardinality_drift_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = copy.deepcopy(_design_response(synthetic_inputs))
    response["resolution_records"][5][
        "effective_authority_record_sha256"
    ] = "0" * 64
    _rehash_resolution_and_response(response, 5)
    _mock_design(monkeypatch, response)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_inputs)

    response = copy.deepcopy(_design_response(synthetic_inputs))
    response["resolution_records"][5][
        "effective_boundary_cardinality"
    ] = 1
    _rehash_resolution_and_response(response, 5)
    _mock_design(monkeypatch, response)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_inputs)


def test_design_not_ready_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = copy.deepcopy(_design_response(synthetic_inputs))
    response[
        "ready_for_authority_and_unified_view_implementation"
    ] = False
    _rehash_resolution_and_response(response)
    _mock_design(monkeypatch, response)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_inputs)


def test_authority_sha_and_sample_order_drift_rejected_independently(
    synthetic_inputs: tuple[bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = _design_response(synthetic_inputs)
    _mock_design(monkeypatch, response)
    invalid_sha = json.loads(synthetic_inputs[2])
    invalid_sha["new_authority_records"][0][
        "multi_boundary_authority_record_sha256"
    ] = "0" * 64
    invalid_sha_payload = _rehash_execution(invalid_sha)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build((*synthetic_inputs[:2], invalid_sha_payload))

    wrong_order = json.loads(synthetic_inputs[2])
    wrong_order["new_authority_records"].reverse()
    wrong_order_payload = _rehash_execution(wrong_order)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build((*synthetic_inputs[:2], wrong_order_payload))


def test_authority_status_and_quarantine_drift_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = _design_response(synthetic_inputs)
    _mock_design(monkeypatch, response)
    for field, value in (
        ("authority_status", "quarantined"),
        ("sample_quarantined", True),
    ):
        execution = json.loads(synthetic_inputs[2])
        execution["new_authority_records"][0][field] = value
        payload = _rehash_execution(execution)
        with pytest.raises(ValueError, match=f"^{ERROR}$"):
            _build((*synthetic_inputs[:2], payload))


@pytest.mark.parametrize("position", (0, 1, 2))
def test_invalid_exact_byte_type_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes],
    position: int,
) -> None:
    invalid = list(synthetic_inputs)
    invalid[position] = bytearray(invalid[position])  # type: ignore[assignment]
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(tuple(invalid))  # type: ignore[arg-type]


def test_exact_platform_path_required(
    synthetic_inputs: tuple[bytes, bytes, bytes],
) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        PUBLIC_FUNCTION(
            source_v1_submission_bundle=synthetic_inputs[0],
            source_v1_ingestion_execution_bundle=synthetic_inputs[1],
            source_multi_boundary_ingestion_execution_bundle=
                synthetic_inputs[2],
            repo_root=str(REPO_ROOT),  # type: ignore[arg-type]
        )


def test_canonical_serialization_failure_is_fail_closed(
    synthetic_inputs: tuple[bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        subject,
        "_ordered_json_bytes",
        lambda _value: (_ for _ in ()).throw(TypeError("synthetic")),
    )
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_inputs)


def test_forbidden_call_budget_and_zero_filesystem_writes(
    synthetic_inputs: tuple[bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {
        "precedence": 0,
        "compiler": 0,
        "adapter": 0,
        "public_interface": 0,
        "private_evaluator": 0,
        "execution_builder": 0,
        "writes": 0,
    }
    original_precedence = (
        precedence_design
        ._reference_design_covapie_current11_unified_authority_precedence_v1
    )

    def counted_precedence(**keywords):
        calls["precedence"] += 1
        return original_precedence(**keywords)

    def forbidden(name: str):
        def fail(*_arguments, **_keywords):
            calls[name] += 1
            raise AssertionError(f"forbidden call: {name}")

        return fail

    monkeypatch.setattr(
        precedence_design,
        "_reference_design_covapie_current11_unified_authority_precedence_v1",
        counted_precedence,
    )
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
    monkeypatch.setattr(
        multi_execution,
        "build_covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1",
        forbidden("execution_builder"),
    )
    for method in ("write_bytes", "write_text", "touch", "mkdir"):
        monkeypatch.setattr(Path, method, forbidden("writes"))

    bundle = json.loads(_build(synthetic_inputs))
    assert bundle["authority_record_count"] == 5
    assert calls == {
        "precedence": 1,
        "compiler": 0,
        "adapter": 0,
        "public_interface": 0,
        "private_evaluator": 0,
        "execution_builder": 0,
        "writes": 0,
    }
