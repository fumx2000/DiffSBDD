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
    covapie_current11_multi_boundary_authority_bundle_v1
    as multi_authority_bundle,
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
from covalent_ext import (
    covapie_current11_unified_effective_authority_view_v1 as subject,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as legacy_design,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FUNCTION = (
    subject.build_covapie_current11_unified_effective_authority_view_v1
)
ERROR = "CURRENT11_UNIFIED_EFFECTIVE_AUTHORITY_VIEW_INVALID"


def _load_precedence_checker():
    path = (
        REPO_ROOT
        / "scripts/check_covapie_current11_multi_boundary_authority_"
        "materialization_and_unified_precedence_design_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "precedence_checker_for_unified_view_tests", path,
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def synthetic_inputs() -> tuple[bytes, bytes, bytes, bytes]:
    inputs = _load_precedence_checker()._synthetic_inputs(REPO_ROOT)
    authority_bundle = (
        multi_authority_bundle
        .build_covapie_current11_multi_boundary_authority_bundle_v1(
            source_v1_submission_bundle=inputs[0],
            source_v1_ingestion_execution_bundle=inputs[1],
            source_multi_boundary_ingestion_execution_bundle=inputs[2],
            repo_root=REPO_ROOT,
        )
    )
    return (*inputs, authority_bundle)


def _build(inputs: tuple[bytes, bytes, bytes, bytes]) -> bytes:
    return PUBLIC_FUNCTION(
        source_v1_submission_bundle=inputs[0],
        source_v1_ingestion_execution_bundle=inputs[1],
        source_multi_boundary_ingestion_execution_bundle=inputs[2],
        source_multi_boundary_authority_bundle=inputs[3],
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
    inputs: tuple[bytes, bytes, bytes, bytes],
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


def _rehash_design(
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


def _rehash_authority_bundle(bundle: dict[str, Any]) -> bytes:
    bundle["multi_boundary_authority_bundle_sha256"] = (
        subject._record_sha256(
            bundle,
            multi_authority_bundle.EXACT16_FIELDS,
            "multi_boundary_authority_bundle_sha256",
        )
    )
    return _ordered_bytes(bundle)


def test_public_api_signature_annotations_constants_and_source_shas() -> None:
    assert subject.__all__ == (
        "build_covapie_current11_unified_effective_authority_view_v1",
    )
    assert subject.UNIFIED_EFFECTIVE_VIEW_VERSION == (
        "covapie_current11_unified_effective_authority_view_v1"
    )
    assert subject.EFFECTIVE_RECORD_VERSION == (
        "covapie_current11_unified_effective_authority_record_v1"
    )
    assert subject.PRECEDENCE_DESIGN_COMMIT == (
        "00c2471ca4fc855985989aea7f948ebbfa1b06f4"
    )
    assert subject.MULTI_BOUNDARY_AUTHORITY_BUNDLE_COMMIT == (
        "ddf3852519cac5eb0d0e50ef919c15ca36fc127a"
    )
    paths_and_shas = (
        (
            REPO_ROOT
            / "src/covalent_ext/covapie_current11_multi_boundary_authority_"
            "materialization_and_unified_precedence_design_v1.py",
            subject.PRECEDENCE_DESIGN_PRODUCTION_SHA256,
        ),
        (
            REPO_ROOT
            / "src/covalent_ext/covapie_current11_multi_boundary_"
            "authority_bundle_v1.py",
            subject.MULTI_BOUNDARY_AUTHORITY_BUNDLE_PRODUCTION_SHA256,
        ),
    )
    for path, expected_sha in paths_and_shas:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_sha

    signature = inspect.signature(PUBLIC_FUNCTION)
    assert tuple(signature.parameters) == (
        "source_v1_submission_bundle",
        "source_v1_ingestion_execution_bundle",
        "source_multi_boundary_ingestion_execution_bundle",
        "source_multi_boundary_authority_bundle",
        "repo_root",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        and parameter.default is inspect.Parameter.empty
        for parameter in signature.parameters.values()
    )
    assert get_type_hints(PUBLIC_FUNCTION) == {
        "source_v1_submission_bundle": bytes,
        "source_v1_ingestion_execution_bundle": bytes,
        "source_multi_boundary_ingestion_execution_bundle": bytes,
        "source_multi_boundary_authority_bundle": bytes,
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
                "import importlib;importlib.import_module("
                "'covalent_ext.covapie_current11_unified_effective_"
                "authority_view_v1')"
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


def test_exact16_exact10_profile_lineage_and_deterministic_transport(
    synthetic_inputs: tuple[bytes, bytes, bytes, bytes],
) -> None:
    first = _build(synthetic_inputs)
    second = _build(synthetic_inputs)
    assert type(first) is bytes
    assert first == second
    assert first and len(first) < 2 * 1024 * 1024
    assert not first.startswith(b"\xef\xbb\xbf")
    assert b"\x00" not in first
    assert b"\n" not in first
    view = subject._strict_json_object(first)
    assert tuple(view) == subject.EXACT16_VIEW_FIELDS
    assert view["unified_effective_authority_view_version"] == (
        subject.UNIFIED_EFFECTIVE_VIEW_VERSION
    )
    assert view["sample_order"] == list(subject._EXPECTED_SAMPLES)
    assert (
        view["effective_authority_record_count"],
        view["effective_legacy_exact_one_count"],
        view["effective_multi_boundary_exact_two_count"],
    ) == (11, 6, 5)
    assert view["source_v1_submission_bundle_filesystem_sha256"] == (
        hashlib.sha256(synthetic_inputs[0]).hexdigest()
    )
    assert view[
        "source_v1_ingestion_execution_bundle_filesystem_sha256"
    ] == hashlib.sha256(synthetic_inputs[1]).hexdigest()
    assert view[
        "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256"
    ] == hashlib.sha256(synthetic_inputs[2]).hexdigest()
    assert view[
        "source_multi_boundary_authority_bundle_filesystem_sha256"
    ] == hashlib.sha256(synthetic_inputs[3]).hexdigest()
    assert view["unified_effective_authority_view_sha256"] == (
        subject._record_sha256(
            view,
            subject.EXACT16_VIEW_FIELDS,
            "unified_effective_authority_view_sha256",
        )
    )
    assert tuple(json.loads(first)) == subject.EXACT16_VIEW_FIELDS
    for record in view["effective_authority_records"]:
        assert tuple(record) == subject.EXACT10_EFFECTIVE_RECORD_FIELDS
        assert record["unified_effective_authority_record_version"] == (
            subject.EFFECTIVE_RECORD_VERSION
        )
        assert record["unified_effective_authority_record_sha256"] == (
            subject._record_sha256(
                record,
                subject.EXACT10_EFFECTIVE_RECORD_FIELDS,
                "unified_effective_authority_record_sha256",
            )
        )


def test_selected_samples_payload_schemas_and_resolution_linkage(
    synthetic_inputs: tuple[bytes, bytes, bytes, bytes],
) -> None:
    response = _design_response(synthetic_inputs)
    resolutions = response["resolution_records"]
    view = json.loads(_build(synthetic_inputs))
    records = view["effective_authority_records"]
    legacy_execution = json.loads(synthetic_inputs[1])
    authority_bundle = json.loads(synthetic_inputs[3])
    legacy_by_sample = {
        record["sample_index_row_id"]: record
        for record in legacy_execution["new_authority_records"]
    }
    multi_by_sample = {
        record["sample_index_row_id"]: record
        for record in authority_bundle["authority_records"]
    }
    assert tuple(
        record["sample_index_row_id"] for record in records
        if record["effective_authority_namespace"]
        == subject._LEGACY_NAMESPACE
    ) == subject._LEGACY_SAMPLES
    assert tuple(
        record["sample_index_row_id"] for record in records
        if record["effective_authority_namespace"] == subject._MULTI_NAMESPACE
    ) == subject._MULTI_SAMPLES
    for effective, resolution in zip(records, resolutions):
        sample = effective["sample_index_row_id"]
        source = (
            legacy_by_sample[sample]
            if sample in subject._LEGACY_SAMPLES
            else multi_by_sample[sample]
        )
        assert effective["effective_authority_record"] == source
        assert tuple(effective["effective_authority_record"]) == (
            legacy_design.AUTHORITY_RECORD_FIELDS
            if sample in subject._LEGACY_SAMPLES
            else multi_design.MULTI_BOUNDARY_AUTHORITY_RECORD_FIELDS
        )
        assert effective["source_resolution_record_sha256"] == (
            resolution[
                "unified_precedence_resolution_record_sha256"
            ]
        )
        assert effective["source_authority_record_sha256"] == (
            resolution["effective_authority_record_sha256"]
        )
        assert (
            effective["effective_authority_namespace"],
            effective["effective_boundary_cardinality"],
            effective["precedence_reason"],
        ) == (
            resolution["effective_authority_namespace"],
            resolution["effective_boundary_cardinality"],
            resolution["precedence_reason"],
        )


def test_committed_authority_validators_and_bundle_execution_equality(
    synthetic_inputs: tuple[bytes, bytes, bytes, bytes],
) -> None:
    view = json.loads(_build(synthetic_inputs))
    legacy_records = [
        record["effective_authority_record"]
        for record in view["effective_authority_records"]
        if record["effective_authority_namespace"]
        == subject._LEGACY_NAMESPACE
    ]
    multi_records = [
        record["effective_authority_record"]
        for record in view["effective_authority_records"]
        if record["effective_authority_namespace"] == subject._MULTI_NAMESPACE
    ]
    for record in legacy_records:
        legacy_design.validate_authority_record(record)
        assert record["authority_status"] == "active"
        assert record["sample_quarantined"] is False
        assert record[
            "exact_one_attachment_boundary_authority_available"
        ] is True
    for record in multi_records:
        multi_design._validate_authority_record(record)
        assert record["authority_status"] == "active"
        assert record["sample_quarantined"] is False
        assert record[
            "exact_two_attachment_boundaries_authority_available"
        ] is True
    assert json.loads(synthetic_inputs[3])["authority_records"] == (
        json.loads(synthetic_inputs[2])["new_authority_records"]
    )


def test_inputs_sources_and_returned_payload_are_isolated(
    synthetic_inputs: tuple[bytes, bytes, bytes, bytes],
) -> None:
    input_snapshots = tuple(bytes(value) for value in synthetic_inputs)
    legacy_snapshot = copy.deepcopy(
        json.loads(synthetic_inputs[1])["new_authority_records"]
    )
    multi_snapshot = copy.deepcopy(
        json.loads(synthetic_inputs[2])["new_authority_records"]
    )
    bundle_snapshot = copy.deepcopy(
        json.loads(synthetic_inputs[3])["authority_records"]
    )
    first = _build(synthetic_inputs)
    decoded = json.loads(first)
    decoded["effective_authority_records"][0][
        "effective_authority_record"
    ]["reviewed_warhead_atom_ids"].append("MUTATION")
    assert decoded["effective_authority_records"][1] != (
        decoded["effective_authority_records"][0]
    )
    assert _build(synthetic_inputs) == first
    assert input_snapshots == synthetic_inputs
    assert legacy_snapshot == json.loads(synthetic_inputs[1])[
        "new_authority_records"
    ]
    assert multi_snapshot == json.loads(synthetic_inputs[2])[
        "new_authority_records"
    ]
    assert bundle_snapshot == json.loads(synthetic_inputs[3])[
        "authority_records"
    ]


def test_precedence_and_validation_helpers_called_once_per_build(
    synthetic_inputs: tuple[bytes, bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    originals = {
        "precedence": precedence_design
        ._reference_design_covapie_current11_unified_authority_precedence_v1,
        "legacy": precedence_design._validate_legacy_execution,
        "multi": precedence_design._validate_multi_execution,
    }
    calls = {key: 0 for key in originals}

    def wrap(name: str):
        def counted(*arguments, **keywords):
            calls[name] += 1
            return originals[name](*arguments, **keywords)

        return counted

    monkeypatch.setattr(
        precedence_design,
        "_reference_design_covapie_current11_unified_authority_precedence_v1",
        wrap("precedence"),
    )
    monkeypatch.setattr(
        precedence_design, "_validate_legacy_execution", wrap("legacy")
    )
    monkeypatch.setattr(
        precedence_design, "_validate_multi_execution", wrap("multi")
    )
    assert json.loads(_build(synthetic_inputs))[
        "effective_authority_record_count"
    ] == 11
    assert calls == {"precedence": 1, "legacy": 1, "multi": 1}


def test_design_digest_missing_resolution_and_not_ready_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = _design_response(synthetic_inputs)
    response[
        "unified_authority_precedence_design_response_sha256"
    ] = "0" * 64
    _mock_design(monkeypatch, response)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_inputs)

    response = _design_response(synthetic_inputs)
    response["resolution_records"] = response["resolution_records"][:-1]
    _rehash_design(response)
    _mock_design(monkeypatch, response)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_inputs)

    response = _design_response(synthetic_inputs)
    response[
        "ready_for_authority_and_unified_view_implementation"
    ] = False
    _rehash_design(response)
    _mock_design(monkeypatch, response)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_inputs)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("effective_authority_namespace", "drifted_namespace"),
        ("effective_boundary_cardinality", 2),
        ("precedence_reason", "DRIFTED_REASON"),
        ("effective_authority_record_sha256", "0" * 64),
    ),
)
def test_resolution_semantic_and_effective_sha_drift_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
) -> None:
    response = copy.deepcopy(_design_response(synthetic_inputs))
    response["resolution_records"][0][field] = value
    _rehash_design(response, 0)
    _mock_design(monkeypatch, response)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_inputs)


def test_duplicate_and_missing_resolution_sample_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = copy.deepcopy(_design_response(synthetic_inputs))
    response["resolution_records"][1]["sample_index_row_id"] = (
        response["resolution_records"][0]["sample_index_row_id"]
    )
    _rehash_design(response, 1)
    _mock_design(monkeypatch, response)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_inputs)

    response = copy.deepcopy(_design_response(synthetic_inputs))
    response["resolution_records"] = (
        *response["resolution_records"][:5],
        *response["resolution_records"][6:],
    )
    _rehash_design(response)
    _mock_design(monkeypatch, response)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_inputs)


@pytest.mark.parametrize(
    ("position", "field", "value"),
    (
        (0, "legacy_v1_authority_status", "quarantined"),
        (5, "legacy_v1_sample_quarantined", False),
        (5, "multi_boundary_authority_status", "quarantined"),
    ),
)
def test_resolution_source_status_drift_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
    position: int,
    field: str,
    value: object,
) -> None:
    response = copy.deepcopy(_design_response(synthetic_inputs))
    response["resolution_records"][position][field] = value
    _rehash_design(response, position)
    _mock_design(monkeypatch, response)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_inputs)


def test_authority_bundle_digest_and_source_lineage_drift_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes, bytes],
) -> None:
    bundle = json.loads(synthetic_inputs[3])
    bundle["multi_boundary_authority_bundle_sha256"] = "0" * 64
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build((*synthetic_inputs[:3], _ordered_bytes(bundle)))

    bundle = json.loads(synthetic_inputs[3])
    bundle[
        "source_v1_ingestion_execution_bundle_filesystem_sha256"
    ] = "0" * 64
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build((*synthetic_inputs[:3], _rehash_authority_bundle(bundle)))


def test_authority_bundle_record_replacement_with_rehash_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes, bytes],
) -> None:
    bundle = json.loads(synthetic_inputs[3])
    bundle["authority_records"][0] = copy.deepcopy(
        bundle["authority_records"][1]
    )
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build((*synthetic_inputs[:3], _rehash_authority_bundle(bundle)))


def test_legacy_and_multi_authority_status_drift_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = _design_response(synthetic_inputs)
    _mock_design(monkeypatch, response)
    legacy_execution = json.loads(synthetic_inputs[1])
    legacy_execution["new_authority_records"][0]["authority_status"] = (
        "quarantined"
    )
    legacy_execution["ingestion_execution_bundle_sha256"] = (
        subject._record_sha256(
            legacy_execution,
            tuple(legacy_execution),
            "ingestion_execution_bundle_sha256",
        )
    )
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build((
            synthetic_inputs[0],
            _ordered_bytes(legacy_execution),
            synthetic_inputs[2],
            synthetic_inputs[3],
        ))

    multi_bundle = json.loads(synthetic_inputs[3])
    multi_bundle["authority_records"][0]["authority_status"] = (
        "quarantined"
    )
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build((*synthetic_inputs[:3], _rehash_authority_bundle(multi_bundle)))


@pytest.mark.parametrize("position", (0, 1, 2, 3))
def test_invalid_exact_byte_type_rejected(
    synthetic_inputs: tuple[bytes, bytes, bytes, bytes],
    position: int,
) -> None:
    invalid = list(synthetic_inputs)
    invalid[position] = bytearray(invalid[position])  # type: ignore[assignment]
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(tuple(invalid))  # type: ignore[arg-type]


def test_exact_platform_path_required(
    synthetic_inputs: tuple[bytes, bytes, bytes, bytes],
) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        PUBLIC_FUNCTION(
            source_v1_submission_bundle=synthetic_inputs[0],
            source_v1_ingestion_execution_bundle=synthetic_inputs[1],
            source_multi_boundary_ingestion_execution_bundle=
                synthetic_inputs[2],
            source_multi_boundary_authority_bundle=synthetic_inputs[3],
            repo_root=str(REPO_ROOT),  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "helper_name", ("_canonical_json_bytes", "_ordered_json_bytes")
)
def test_serialization_failure_is_fail_closed(
    synthetic_inputs: tuple[bytes, bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
    helper_name: str,
) -> None:
    monkeypatch.setattr(
        subject,
        helper_name,
        lambda _value: (_ for _ in ()).throw(TypeError("synthetic")),
    )
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _build(synthetic_inputs)


def test_forbidden_calls_and_filesystem_writes_are_zero(
    synthetic_inputs: tuple[bytes, bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {
        "precedence": 0,
        "legacy_validation": 0,
        "multi_validation": 0,
        "authority_builder": 0,
        "compiler": 0,
        "adapter": 0,
        "public_interface": 0,
        "private_evaluator": 0,
        "execution_builder": 0,
        "writes": 0,
    }
    originals = {
        "precedence": precedence_design
        ._reference_design_covapie_current11_unified_authority_precedence_v1,
        "legacy_validation": precedence_design._validate_legacy_execution,
        "multi_validation": precedence_design._validate_multi_execution,
    }

    def counted(name: str):
        def call(*arguments, **keywords):
            calls[name] += 1
            return originals[name](*arguments, **keywords)

        return call

    def forbidden(name: str):
        def fail(*_arguments, **_keywords):
            calls[name] += 1
            raise AssertionError(f"forbidden call: {name}")

        return fail

    monkeypatch.setattr(
        precedence_design,
        "_reference_design_covapie_current11_unified_authority_precedence_v1",
        counted("precedence"),
    )
    monkeypatch.setattr(
        precedence_design,
        "_validate_legacy_execution",
        counted("legacy_validation"),
    )
    monkeypatch.setattr(
        precedence_design,
        "_validate_multi_execution",
        counted("multi_validation"),
    )
    monkeypatch.setattr(
        multi_authority_bundle,
        "build_covapie_current11_multi_boundary_authority_bundle_v1",
        forbidden("authority_builder"),
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

    assert json.loads(_build(synthetic_inputs))[
        "effective_authority_record_count"
    ] == 11
    assert calls == {
        "precedence": 1,
        "legacy_validation": 1,
        "multi_validation": 1,
        "authority_builder": 0,
        "compiler": 0,
        "adapter": 0,
        "public_interface": 0,
        "private_evaluator": 0,
        "execution_builder": 0,
        "writes": 0,
    }
