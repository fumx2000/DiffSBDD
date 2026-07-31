from __future__ import annotations

import builtins
import copy
import csv
import hashlib
import importlib.util
import inspect
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import pytest

from covalent_ext import (
    covapie_current11_multi_boundary_authority_bundle_v1 as multi_authority,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_submission_adapter_v1 as adapter,
)
from covalent_ext import (
    covapie_current11_unified_effective_authority_view_v1 as unified_view,
)
from covalent_ext import (
    covapie_target_residue_atom_condition_contract_design_v1 as contract_design,
)
from covalent_ext import (
    covapie_current11_target_residue_atom_condition_source_inventory_v1 as subject,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_checker():
    path = REPO_ROOT / "scripts/check_covapie_current11_target_residue_atom_condition_source_inventory_v1.py"
    specification = importlib.util.spec_from_file_location(
        "source_inventory_checker_for_tests", path
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


CHECKER = _load_checker()


@pytest.fixture(scope="module")
def synthetic_view() -> bytes:
    return CHECKER._synthetic_view(REPO_ROOT)


@pytest.fixture(autouse=True)
def accept_synthetic_view(
    monkeypatch: pytest.MonkeyPatch, synthetic_view: bytes
) -> None:
    view = json.loads(synthetic_view)
    monkeypatch.setattr(
        contract_design,
        "_FORMAL_VIEW_FILESYSTEM_SHA256",
        hashlib.sha256(synthetic_view).hexdigest(),
    )
    monkeypatch.setattr(
        contract_design,
        "_FORMAL_VIEW_INTERNAL_SHA256",
        view["unified_effective_authority_view_sha256"],
    )


def _build(source: bytes, root: Path) -> bytes:
    return subject.build_covapie_current11_target_residue_atom_condition_source_inventory_v1(
        source_unified_effective_authority_view=source,
        repo_root=root,
    )


def _fixture(
    root: Path,
    source: bytes,
    situations: dict[int, str] | None = None,
) -> None:
    CHECKER._fixture_repo(root, source, situations)


def _read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), [dict(row) for row in reader]


def _sample_csv(root: Path) -> Path:
    return root / contract_design._SAMPLE_INDEX_PATH


def _rewrite_sample(
    root: Path,
    transform: Callable[[tuple[str, ...], list[dict[str, str]]], tuple[tuple[str, ...], list[dict[str, str]]]],
) -> None:
    fields, rows = _read_csv(_sample_csv(root))
    fields, rows = transform(fields, rows)
    CHECKER._write_csv(_sample_csv(root), fields, rows)


def _decoded(source: bytes, root: Path) -> dict[str, Any]:
    return json.loads(_build(source, root))


def _first_artifact(value: dict[str, Any], role: str) -> dict[str, Any]:
    return next(
        record
        for record in value["source_inventory_records"][0][
            "source_artifact_status_records"
        ]
        if record["artifact_role"] == role
    )


def _first_observation(value: dict[str, Any], field: str) -> dict[str, Any]:
    return next(
        record
        for record in value["source_inventory_records"][0][
            "field_observation_records"
        ]
        if record["field_name"] == field
    )


def test_public_api_signature_annotations_constants_and_import_silence() -> None:
    assert subject.__all__ == (
        "build_covapie_current11_target_residue_atom_condition_source_inventory_v1",
    )
    signature = inspect.signature(
        subject.build_covapie_current11_target_residue_atom_condition_source_inventory_v1
    )
    assert tuple(signature.parameters) == (
        "source_unified_effective_authority_view",
        "repo_root",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert signature.parameters[
        "source_unified_effective_authority_view"
    ].annotation == "bytes"
    assert signature.parameters["repo_root"].annotation == "Path"
    assert signature.return_annotation == "bytes"
    assert subject.SOURCE_INVENTORY_VERSION == "covapie_current11_target_residue_atom_condition_source_inventory_v1"
    assert subject.FIELD_OBSERVATION_VERSION == "covapie_target_residue_atom_condition_source_field_observation_v1"
    assert subject.ARTIFACT_STATUS_VERSION == "covapie_target_residue_atom_condition_source_artifact_status_v1"
    assert subject.SAMPLE_INVENTORY_RECORD_VERSION == "covapie_current11_target_residue_atom_condition_source_inventory_record_v1"
    assert subject.CONTRACT_DESIGN_COMMIT == "fb59a976f6faaa58829f9a761ae4634bcb05a273"
    assert subject.CONTRACT_DESIGN_PRODUCTION_SHA256 == hashlib.sha256(
        Path(contract_design.__file__).read_bytes()
    ).hexdigest()
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "from covalent_ext import covapie_current11_target_residue_atom_condition_source_inventory_v1",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == ""


def test_exact9_exact10_exact18_exact24_order_counts_and_digests(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture(tmp_path, synthetic_view)
    payload = _build(synthetic_view, tmp_path)
    assert type(payload) is bytes
    value = json.loads(payload)
    assert tuple(value) == subject.SOURCE_INVENTORY_BUNDLE_FIELDS
    assert len(value) == 24
    assert value["sample_order"] == list(subject._EXPECTED_SAMPLES)
    assert value["future_source_inventory_required_fields"] == list(
        contract_design._FUTURE_SOURCE_INVENTORY_REQUIRED_FIELDS
    )
    assert len(value["future_source_inventory_required_fields"]) == 21
    assert len(value["source_inventory_records"]) == 11
    assert value["source_inventory_bundle_sha256"] == subject._record_sha256(
        value,
        subject.SOURCE_INVENTORY_BUNDLE_FIELDS,
        "source_inventory_bundle_sha256",
    )
    for record in value["source_inventory_records"]:
        assert tuple(record) == subject.SAMPLE_INVENTORY_RECORD_FIELDS
        assert len(record) == 18
        assert len(record["field_observation_records"]) == 21
        assert len(record["source_artifact_status_records"]) == 3
        assert record["source_inventory_record_sha256"] == subject._record_sha256(
            record,
            subject.SAMPLE_INVENTORY_RECORD_FIELDS,
            "source_inventory_record_sha256",
        )
        for observation in record["field_observation_records"]:
            assert tuple(observation) == subject.FIELD_OBSERVATION_RECORD_FIELDS
            assert observation["field_observation_record_sha256"] == subject._record_sha256(
                observation,
                subject.FIELD_OBSERVATION_RECORD_FIELDS,
                "field_observation_record_sha256",
            )
        for artifact in record["source_artifact_status_records"]:
            assert tuple(artifact) == subject.ARTIFACT_STATUS_RECORD_FIELDS
            assert artifact["artifact_status_record_sha256"] == subject._record_sha256(
                artifact,
                subject.ARTIFACT_STATUS_RECORD_FIELDS,
                "artifact_status_record_sha256",
            )
    assert b"\n" not in payload and b"\r" not in payload
    assert len(payload) < 4 * 1024 * 1024
    assert json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode() == payload


def test_design_called_exactly_once_and_coverage_is_copied_record_by_record(
    synthetic_view: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fixture(tmp_path, synthetic_view, {1: "schema_incomplete"})
    original = contract_design._reference_design_covapie_target_residue_atom_condition_contract_v1
    expected = original(
        source_unified_effective_authority_view=synthetic_view,
        repo_root=tmp_path,
    )
    calls = 0

    def wrapped(**kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return original(**kwargs)

    monkeypatch.setattr(
        contract_design,
        "_reference_design_covapie_target_residue_atom_condition_contract_v1",
        wrapped,
    )
    value = _decoded(synthetic_view, tmp_path)
    assert calls == 1
    for inventory, coverage in zip(
        value["source_inventory_records"], expected["sample_coverage_records"]
    ):
        assert (
            inventory["sample_index_row_id"],
            inventory["pdb_id"],
            inventory["coverage_status"],
            inventory["blocking_reasons"],
            inventory["ready_for_authority_materialization"],
        ) == (
            coverage["sample_index_row_id"],
            coverage["pdb_id"],
            coverage["coverage_status"],
            list(coverage["blocking_reasons"]),
            coverage["ready_for_authority_materialization"],
        )


def test_sample_index_change_after_design_is_rejected(
    synthetic_view: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fixture(tmp_path, synthetic_view)
    sample_path = _sample_csv(tmp_path)
    original = contract_design._reference_design_covapie_target_residue_atom_condition_contract_v1

    def stale_snapshot(**kwargs: Any) -> dict[str, Any]:
        response = original(**kwargs)
        sample_path.write_bytes(sample_path.read_bytes() + b"\n")
        return response

    monkeypatch.setattr(
        contract_design,
        "_reference_design_covapie_target_residue_atom_condition_contract_v1",
        stale_snapshot,
    )
    with pytest.raises(ValueError, match=subject._ERROR):
        _build(synthetic_view, tmp_path)


def test_locator_sidecar_change_after_design_is_rejected(
    synthetic_view: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fixture(tmp_path, synthetic_view)
    locator_path = tmp_path / contract_design._LOCATOR_SIDECAR_PATH
    original = contract_design._reference_design_covapie_target_residue_atom_condition_contract_v1

    def stale_snapshot(**kwargs: Any) -> dict[str, Any]:
        response = original(**kwargs)
        locator_path.write_bytes(locator_path.read_bytes() + b"\n")
        return response

    monkeypatch.setattr(
        contract_design,
        "_reference_design_covapie_target_residue_atom_condition_contract_v1",
        stale_snapshot,
    )
    with pytest.raises(ValueError, match=subject._ERROR):
        _build(synthetic_view, tmp_path)


def test_stale_sample_index_candidate_sha_is_rejected_after_rehash(
    synthetic_view: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fixture(tmp_path, synthetic_view)
    original = contract_design._reference_design_covapie_target_residue_atom_condition_contract_v1

    def stale_candidate(**kwargs: Any) -> dict[str, Any]:
        response = copy.deepcopy(original(**kwargs))
        candidate = next(
            item
            for item in response["source_candidate_records"]
            if item["source_candidate_name"]
            == "current11_sample_index_and_referenced_protein_atom_tables"
        )
        candidate["source_sha256"] = "0" * 64
        candidate["source_candidate_record_sha256"] = subject._record_sha256(
            candidate,
            contract_design._SOURCE_CANDIDATE_FIELDS,
            "source_candidate_record_sha256",
        )
        response["design_response_sha256"] = subject._record_sha256(
            response,
            contract_design._RESPONSE_FIELDS,
            "design_response_sha256",
        )
        return response

    monkeypatch.setattr(
        contract_design,
        "_reference_design_covapie_target_residue_atom_condition_contract_v1",
        stale_candidate,
    )
    with pytest.raises(ValueError, match=subject._ERROR):
        _build(synthetic_view, tmp_path)


def test_locator_candidate_presence_drift_is_rejected_in_both_directions(
    synthetic_view: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    declared_root = tmp_path / "declared_but_missing"
    undeclared_root = tmp_path / "undeclared_but_present"
    _fixture(declared_root, synthetic_view)
    _fixture(undeclared_root, synthetic_view)
    original = contract_design._reference_design_covapie_target_residue_atom_condition_contract_v1
    declared_locator = declared_root / contract_design._LOCATOR_SIDECAR_PATH

    def remove_after_design(**kwargs: Any) -> dict[str, Any]:
        response = original(**kwargs)
        declared_locator.unlink()
        return response

    monkeypatch.setattr(
        contract_design,
        "_reference_design_covapie_target_residue_atom_condition_contract_v1",
        remove_after_design,
    )
    with pytest.raises(ValueError, match=subject._ERROR):
        _build(synthetic_view, declared_root)

    undeclared_locator = undeclared_root / contract_design._LOCATOR_SIDECAR_PATH
    locator_payload = undeclared_locator.read_bytes()

    def add_after_design(**kwargs: Any) -> dict[str, Any]:
        undeclared_locator.unlink()
        response = original(**kwargs)
        undeclared_locator.write_bytes(locator_payload)
        return response

    monkeypatch.setattr(
        contract_design,
        "_reference_design_covapie_target_residue_atom_condition_contract_v1",
        add_after_design,
    )
    with pytest.raises(ValueError, match=subject._ERROR):
        _build(synthetic_view, undeclared_root)


def test_present_missing_column_and_missing_value_observations(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture(tmp_path, synthetic_view)
    present = _first_observation(_decoded(synthetic_view, tmp_path), "pdb_id")
    assert present["column_present"] is True
    assert present["observation_status"] == "present_nonempty"

    def remove_column(fields: tuple[str, ...], rows: list[dict[str, str]]):
        new_fields = tuple(field for field in fields if field != "protein_type_symbol")
        for row in rows:
            row.pop("protein_type_symbol")
        return new_fields, rows

    _rewrite_sample(tmp_path, remove_column)
    missing_column = _first_observation(
        _decoded(synthetic_view, tmp_path), "protein_type_symbol"
    )
    assert missing_column["column_present"] is False
    assert missing_column["observation_status"] == "missing_column"

    def empty_value(fields: tuple[str, ...], rows: list[dict[str, str]]):
        rows[0]["protein_type_symbol"] = ""
        return fields, rows

    _fixture(tmp_path, synthetic_view)
    _rewrite_sample(tmp_path, empty_value)
    missing_value = _first_observation(
        _decoded(synthetic_view, tmp_path), "protein_type_symbol"
    )
    assert missing_value["column_present"] is True
    assert missing_value["observation_status"] == "missing_value"


def test_insertion_question_and_altloc_dot_require_explicit_provenance_and_b_is_preserved(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture(tmp_path, synthetic_view)
    value = _decoded(synthetic_view, tmp_path)
    insertion = _first_observation(value, "protein_pdbx_PDB_ins_code")
    altloc_b = _first_observation(value, "protein_label_alt_id")
    altloc_dot = next(
        item
        for item in value["source_inventory_records"][1]["field_observation_records"]
        if item["field_name"] == "protein_label_alt_id"
    )
    assert insertion["raw_value"] == insertion["normalised_value"] == ""
    assert insertion["observation_status"] == "present_normalised_empty_with_explicit_provenance"
    assert altloc_dot["observation_status"] == "present_normalised_empty_with_explicit_provenance"
    assert altloc_b["raw_value"] == altloc_b["normalised_value"] == "B"
    assert altloc_b["observation_status"] == "present_nonempty"

    def raw_question(fields: tuple[str, ...], rows: list[dict[str, str]]):
        rows[0]["protein_pdbx_PDB_ins_code"] = "?"
        return fields, rows

    _rewrite_sample(tmp_path, raw_question)
    question = _first_observation(
        _decoded(synthetic_view, tmp_path), "protein_pdbx_PDB_ins_code"
    )
    assert question["raw_value"] == "?"
    assert question["normalised_value"] == ""


def test_empty_insertion_and_altloc_without_source_provenance_are_rejected(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture(tmp_path, synthetic_view)
    table = tmp_path / "synthetic/atom/CYS_SG_SAMPLE_INDEX_000001.csv"
    fields, rows = _read_csv(table)
    rows[0]["pdbx_PDB_ins_code"] = ""
    rows[0]["label_alt_id"] = ""
    CHECKER._write_csv(table, fields, rows)
    locator = tmp_path / contract_design._LOCATOR_SIDECAR_PATH
    locator_fields, locator_rows = _read_csv(locator)
    locator_rows[0]["atom_site_insertion_raw_value"] = ""
    CHECKER._write_csv(locator, locator_fields, locator_rows)

    def empty_altloc(fields: tuple[str, ...], rows: list[dict[str, str]]):
        rows[0]["protein_label_alt_id"] = ""
        rows[0]["protein_pdbx_PDB_ins_code"] = "?"
        return fields, rows

    _rewrite_sample(tmp_path, empty_altloc)
    value = _decoded(synthetic_view, tmp_path)
    assert _first_observation(value, "protein_pdbx_PDB_ins_code")[
        "observation_status"
    ] == "missing_normalisation_provenance"
    assert _first_observation(value, "protein_label_alt_id")[
        "observation_status"
    ] == "missing_normalisation_provenance"


def test_structure_condition_evidence_and_atom_table_digests_are_recomputed(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture(tmp_path, synthetic_view)
    value = _decoded(synthetic_view, tmp_path)
    structure = _first_artifact(value, "source_structure")
    evidence = _first_artifact(value, "condition_evidence")
    table = _first_artifact(value, "protein_atom_table")
    assert structure["recomputed_sha256"] == hashlib.sha256(
        (tmp_path / structure["declared_locator"]).read_bytes()
    ).hexdigest()
    evidence_value = json.loads((tmp_path / evidence["declared_locator"]).read_bytes())
    assert evidence["recomputed_sha256"] == subject._record_sha256(
        evidence_value,
        contract_design._CONDITION_EVIDENCE_RECORD_FIELDS,
        "condition_evidence_record_sha256",
    )
    assert table["recomputed_sha256"] == hashlib.sha256(
        (tmp_path / table["declared_locator"]).read_bytes()
    ).hexdigest()
    assert structure["artifact_status"] == evidence["artifact_status"] == "available_verified"
    assert table["artifact_status"] == "available_unverified"


def test_structure_digest_mismatch_and_declared_file_missing(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    mismatch_root = tmp_path / "mismatch"
    missing_root = tmp_path / "missing"
    _fixture(mismatch_root, synthetic_view, {1: "structure_digest_mismatch"})
    _fixture(missing_root, synthetic_view, {1: "missing_structure"})
    mismatch = _first_artifact(
        _decoded(synthetic_view, mismatch_root), "source_structure"
    )
    missing = _first_artifact(
        _decoded(synthetic_view, missing_root), "source_structure"
    )
    assert mismatch["digest_match_status"] == "mismatched"
    assert mismatch["artifact_status"] == "digest_mismatch"
    assert missing["digest_match_status"] == "not_available"
    assert missing["artifact_status"] == "declared_file_missing"


def test_condition_evidence_digest_mismatch_missing_file_and_inline_json(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    mismatch_root = tmp_path / "mismatch"
    missing_root = tmp_path / "missing"
    inline_root = tmp_path / "inline"
    for root in (mismatch_root, missing_root, inline_root):
        _fixture(root, synthetic_view)

    def mismatch_digest(fields: tuple[str, ...], rows: list[dict[str, str]]):
        rows[0]["source_condition_evidence_sha256"] = "0" * 64
        return fields, rows

    _rewrite_sample(mismatch_root, mismatch_digest)
    missing_path = missing_root / "synthetic/evidence/CYS_SG_SAMPLE_INDEX_000001.json"
    missing_path.unlink()

    def inline(fields: tuple[str, ...], rows: list[dict[str, str]]):
        evidence_path = inline_root / rows[0]["source_condition_evidence_path_or_record"]
        rows[0]["source_condition_evidence_path_or_record"] = evidence_path.read_text(encoding="utf-8")
        return fields, rows

    _rewrite_sample(inline_root, inline)
    mismatch = _first_artifact(
        _decoded(synthetic_view, mismatch_root), "condition_evidence"
    )
    missing = _first_artifact(
        _decoded(synthetic_view, missing_root), "condition_evidence"
    )
    inline_record = _first_artifact(
        _decoded(synthetic_view, inline_root), "condition_evidence"
    )
    assert mismatch["artifact_status"] == "digest_mismatch"
    assert missing["artifact_status"] == "declared_file_missing"
    assert inline_record["locator_kind"] == "inline_json"
    assert inline_record["artifact_status"] == "available_verified"


def test_invalid_evidence_payload_is_recorded_fail_closed(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture(tmp_path, synthetic_view)
    evidence = tmp_path / "synthetic/evidence/CYS_SG_SAMPLE_INDEX_000001.json"
    evidence.write_text('{"duplicate":1,"duplicate":2}', encoding="utf-8")
    artifact = _first_artifact(
        _decoded(synthetic_view, tmp_path), "condition_evidence"
    )
    assert artifact["artifact_available"] is True
    assert artifact["artifact_status"] == "invalid_payload"


@pytest.mark.parametrize("locator", ["/absolute/structure.cif", "../escape.cif"])
def test_absolute_and_traversal_paths_are_unsafe(
    synthetic_view: bytes, tmp_path: Path, locator: str
) -> None:
    _fixture(tmp_path, synthetic_view)

    def unsafe(fields: tuple[str, ...], rows: list[dict[str, str]]):
        rows[0]["source_structure_path"] = locator
        return fields, rows

    _rewrite_sample(tmp_path, unsafe)
    artifact = _first_artifact(
        _decoded(synthetic_view, tmp_path), "source_structure"
    )
    assert artifact["locator_kind"] == "unsafe"
    assert artifact["artifact_status"] == "unsafe_path"


def test_symlink_is_rejected_as_authority_source(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture(tmp_path, synthetic_view)
    structure = tmp_path / "synthetic/structure/CYS_SG_SAMPLE_INDEX_000001.cif"
    payload = structure.read_bytes()
    target = tmp_path.parent / "same-bytes-target-outside-fixture.cif"
    target.write_bytes(payload)
    structure.unlink()
    structure.symlink_to(target)
    artifact = _first_artifact(
        _decoded(synthetic_view, tmp_path), "source_structure"
    )
    assert artifact["artifact_available"] is False
    assert artifact["artifact_status"] == "symlink_rejected"


def test_locator_sidecar_does_not_promote_ready_and_drift_is_not_silent(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture(tmp_path, synthetic_view, {1: "schema_incomplete"})
    first = _decoded(synthetic_view, tmp_path)["source_inventory_records"][0]
    assert first["locator_sidecar_match_count"] == 1
    assert first["locator_matched_atom_site_ids"] == ["ATOM-1"]
    assert first["ready_for_authority_materialization"] is False

    _fixture(tmp_path, synthetic_view)

    def drift(fields: tuple[str, ...], rows: list[dict[str, str]]):
        rows[0]["source_atom_site_id"] = "DRIFTED"
        return fields, rows

    _rewrite_sample(tmp_path, drift)
    drifted = _decoded(synthetic_view, tmp_path)["source_inventory_records"][0]
    assert drifted["coverage_status"] == "lineage_mismatch"
    assert "source_inventory_sample_atom_lineage_mismatch" in drifted[
        "blocking_reasons"
    ]


def test_sample_index_row_digest_uses_canonical_row_not_csv_line_number(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture(tmp_path, synthetic_view)
    fields, rows = _read_csv(_sample_csv(tmp_path))
    expected = hashlib.sha256(subject._canonical_json_bytes(rows[0])).hexdigest()
    first = _decoded(synthetic_view, tmp_path)["source_inventory_records"][0]
    assert first["sample_index_row_sha256"] == expected
    CHECKER._write_csv(_sample_csv(tmp_path), fields, list(reversed(rows)))
    reordered = _decoded(synthetic_view, tmp_path)["source_inventory_records"]
    assert [record["sample_index_row_id"] for record in reordered] == list(
        subject._EXPECTED_SAMPLES
    )
    assert reordered[0]["sample_index_row_sha256"] == expected


def test_deterministic_inputs_unchanged_returned_payload_isolated_and_zero_writes(
    synthetic_view: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fixture(tmp_path, synthetic_view)
    before = CHECKER._tree_snapshot(tmp_path)
    source_snapshot = bytes(synthetic_view)

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("filesystem write attempted")

    monkeypatch.setattr(Path, "write_bytes", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(Path, "touch", forbidden)
    monkeypatch.setattr(Path, "mkdir", forbidden)
    first = _build(synthetic_view, tmp_path)
    decoded = json.loads(first)
    decoded["sample_order"][0] = "MUTATED"
    second = _build(synthetic_view, tmp_path)
    assert first == second
    assert json.loads(second)["sample_order"][0] == subject._EXPECTED_SAMPLES[0]
    assert synthetic_view == source_snapshot
    assert CHECKER._tree_snapshot(tmp_path) == before


def test_forbidden_builders_adapter_and_model_are_not_called(
    synthetic_view: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fixture(tmp_path, synthetic_view)

    def forbidden(*args: Any, **kwargs: Any) -> bytes:
        raise AssertionError("forbidden call")

    monkeypatch.setattr(
        unified_view,
        "build_covapie_current11_unified_effective_authority_view_v1",
        forbidden,
    )
    monkeypatch.setattr(
        multi_authority,
        "build_covapie_current11_multi_boundary_authority_bundle_v1",
        forbidden,
    )
    monkeypatch.setattr(
        adapter,
        "adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1",
        forbidden,
    )
    assert _build(synthetic_view, tmp_path)
    source = Path(subject.__file__).read_text(encoding="utf-8")
    assert "lightning_modules" not in source
    assert "equivariant_diffusion" not in source
    assert "loss(" not in source


def test_malformed_unified_view_and_wrong_exact_argument_types_are_rejected(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture(tmp_path, synthetic_view)
    with pytest.raises(ValueError, match=subject._ERROR):
        _build(synthetic_view + b"\n", tmp_path)
    with pytest.raises(ValueError, match=subject._ERROR):
        subject.build_covapie_current11_target_residue_atom_condition_source_inventory_v1(
            source_unified_effective_authority_view=bytearray(synthetic_view),
            repo_root=tmp_path,
        )
    with pytest.raises(ValueError, match=subject._ERROR):
        subject.build_covapie_current11_target_residue_atom_condition_source_inventory_v1(
            source_unified_effective_authority_view=synthetic_view,
            repo_root=str(tmp_path),
        )


def test_malformed_csv_and_duplicate_sample_rows_are_rejected(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    malformed_root = tmp_path / "malformed"
    duplicate_root = tmp_path / "duplicate"
    _fixture(malformed_root, synthetic_view)
    _fixture(duplicate_root, synthetic_view)
    table = malformed_root / "synthetic/atom/CYS_SG_SAMPLE_INDEX_000001.csv"
    table.write_bytes(b'a,b\n"unterminated,1\n')
    with pytest.raises(ValueError, match=subject._ERROR):
        _build(synthetic_view, malformed_root)
    fields, rows = _read_csv(_sample_csv(duplicate_root))
    rows.append(dict(rows[0]))
    CHECKER._write_csv(_sample_csv(duplicate_root), fields, rows)
    with pytest.raises(ValueError, match=subject._ERROR):
        _build(synthetic_view, duplicate_root)


def test_illegal_design_status_vocabulary_is_rejected_even_with_valid_digests(
    synthetic_view: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fixture(tmp_path, synthetic_view)
    original = contract_design._reference_design_covapie_target_residue_atom_condition_contract_v1

    def illegal(**kwargs: Any) -> dict[str, Any]:
        response = copy.deepcopy(original(**kwargs))
        coverage = response["sample_coverage_records"][0]
        coverage["coverage_status"] = "illegal_status"
        coverage["sample_coverage_record_sha256"] = subject._record_sha256(
            coverage,
            contract_design._SAMPLE_COVERAGE_FIELDS,
            "sample_coverage_record_sha256",
        )
        response["design_response_sha256"] = subject._record_sha256(
            response,
            contract_design._RESPONSE_FIELDS,
            "design_response_sha256",
        )
        return response

    monkeypatch.setattr(
        contract_design,
        "_reference_design_covapie_target_residue_atom_condition_contract_v1",
        illegal,
    )
    with pytest.raises(ValueError, match=subject._ERROR):
        _build(synthetic_view, tmp_path)


def test_serialization_failure_fails_closed(
    synthetic_view: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fixture(tmp_path, synthetic_view)

    def fail(_: dict[str, Any]) -> bytes:
        raise TypeError("synthetic serialization failure")

    monkeypatch.setattr(subject, "_transport", fail)
    with pytest.raises(ValueError, match=subject._ERROR):
        _build(synthetic_view, tmp_path)


def test_production_source_contains_no_write_operations_or_extra_public_builder() -> None:
    source = Path(subject.__file__).read_text(encoding="utf-8")
    forbidden = (
        ".write_bytes(",
        ".write_text(",
        ".touch(",
        ".mkdir(",
        "os.rename(",
        "os.replace(",
    )
    assert all(token not in source for token in forbidden)
    assert source.count(
        "def build_covapie_current11_target_residue_atom_condition_source_inventory_v1("
    ) == 1
    assert builtins.open is open
