"""System and fail-closed tests for Step14AU-E0-P6-B0 revised1."""
from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_residue_locator_historical_raw_fingerprint_authority_consolidation_gate
    as gate,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate
    as p6a,
)

CHECK_PATH = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_covalent_residue_locator_historical_raw_fingerprint_authority_consolidation_gate_v1.py"
MODULE_PATH = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_historical_raw_fingerprint_authority_consolidation_gate.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("p6b0_checker", CHECK_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _materialize(tmp_path: Path, forced: tuple[str, ...] = ()) -> Path:
    root = tmp_path / "outputs"
    gate.run_covapie_bulk_download_admission_covalent_residue_locator_historical_raw_fingerprint_authority_consolidation_gate_v1(root, forced)
    return root


def _hashes(root: Path) -> dict[str, str]:
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in gate.OUTPUT_FILES}


def _documents() -> dict[str, gate.CsvDocument]:
    return copy.deepcopy(gate._historical_documents())


def _replace_rows(
    documents: dict[str, gate.CsvDocument], role: str, rows: list[dict[str, str]]
) -> dict[str, gate.CsvDocument]:
    document = documents[role]
    documents[role] = gate.CsvDocument(document.header, tuple(rows), document.status, document.blocking_reason)
    return documents


def _mutate_target(
    documents: dict[str, gate.CsvDocument], role: str, pdb_id: str,
    field: str, value: str,
) -> dict[str, gate.CsvDocument]:
    rows = [dict(row) for row in documents[role].rows]
    for row in rows:
        if row["pdb_id"] == pdb_id:
            row[field] = value
            break
    return _replace_rows(documents, role, rows)


def _binding_document() -> gate.CsvDocument:
    return copy.deepcopy(gate._p6a_inputs()[1])


def test_import_has_no_materialization_side_effect(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import covalent_ext.covapie_bulk_download_admission_covalent_residue_locator_historical_raw_fingerprint_authority_consolidation_gate"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(REPO_ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout == result.stderr == "" and not list(tmp_path.iterdir())


def test_exact_outputs_double_materialization_and_no_tmp(tmp_path: Path) -> None:
    root = _materialize(tmp_path)
    first = _hashes(root)
    gate.run_covapie_bulk_download_admission_covalent_residue_locator_historical_raw_fingerprint_authority_consolidation_gate_v1(root)
    assert _hashes(root) == first
    assert {path.name for path in root.iterdir()} == set(gate.OUTPUT_FILES)
    assert not list(root.glob("*.tmp"))


def test_outputs_have_no_nondeterminism_absolute_path_or_self_hash(tmp_path: Path) -> None:
    root = _materialize(tmp_path)
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.iterdir())
    assert "timestamp" not in text.lower()
    assert str(REPO_ROOT) not in text
    assert "manifest_sha256" not in text


@pytest.mark.parametrize("kind", ["symlink", "file"])
def test_output_root_rejects_symlink_or_nondirectory(tmp_path: Path, kind: str) -> None:
    root = tmp_path / "outputs"
    if kind == "symlink":
        target = tmp_path / "target"
        target.mkdir()
        root.symlink_to(target, target_is_directory=True)
    else:
        root.write_text("not a directory", encoding="utf-8")
    with pytest.raises(RuntimeError, match="OUTPUT_ROOT_NOT_REGULAR_DIRECTORY"):
        gate.run_covapie_bulk_download_admission_covalent_residue_locator_historical_raw_fingerprint_authority_consolidation_gate_v1(root)


def test_atomic_replace_is_used(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[tuple[Path, Path]] = []
    original = os.replace
    monkeypatch.setattr(gate.os, "replace", lambda source, target: (calls.append((Path(source), Path(target))), original(source, target))[1])
    root = _materialize(tmp_path)
    assert len(calls) == 6
    assert all(source.name == target.name + ".tmp" for source, target in calls)
    assert not list(root.glob("*.tmp"))


def test_source_boundary_exact_and_canonical() -> None:
    rows = gate._source_rows()
    assert gate.validate_source_rows(rows)
    assert len(rows) == 10
    assert [row["source_relative_path"] for row in rows] == [str(path) for path in gate.SOURCE_PATHS]


@pytest.mark.parametrize("mutation", ["missing", "extra", "reorder", "expected_hash", "observed_hash", "untracked", "nonregular", "symlink"])
def test_source_boundary_drift_fails(mutation: str) -> None:
    rows = copy.deepcopy(gate._source_rows())
    if mutation == "missing": rows.pop()
    elif mutation == "extra": rows.append(copy.deepcopy(rows[-1]))
    elif mutation == "reorder": rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "expected_hash": rows[0]["sha256_expected"] = "0" * 64
    elif mutation == "observed_hash": rows[0]["sha256_observed"] = "0" * 64
    elif mutation == "untracked": rows[0]["tracked"] = False
    elif mutation == "nonregular": rows[0]["regular_file"] = False
    else: rows[0]["symlink"] = True
    assert not gate.validate_source_rows(rows)


def test_source_sha_constant_drift_fails_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    changed = dict(gate.SOURCE_SHA256)
    changed[str(gate.SOURCE_PATHS[0])] = "0" * 64
    monkeypatch.setattr(gate, "SOURCE_SHA256", changed)
    assert not gate.validate_source_rows(gate._source_rows())


def test_source_boundary_failure_short_circuits_all_production_readers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = copy.deepcopy(gate._source_rows())
    rows[0]["source_check_passed"] = False
    monkeypatch.setattr(gate, "_source_rows", lambda: rows)
    monkeypatch.setattr(
        gate, "_p6a_inputs",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("P6-A source read")),
    )
    monkeypatch.setattr(
        gate, "_historical_documents",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("historical source read")),
    )
    state = gate.build_authority_state()
    assert state["all_checks_passed"] is False
    assert state["authority_rows"] == []
    assert state["sections"] == {
        "source_boundary": False,
        "p6a_predecessor": False,
        "source_role_contract": False,
        "authority_rows": False,
        "authority_contract": False,
        "issue_inventory": True,
        "safety": True,
    }


def test_forced_source_boundary_failure_short_circuits_readers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        gate, "_p6a_inputs",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("P6-A source read")),
    )
    monkeypatch.setattr(
        gate, "_historical_documents",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("historical source read")),
    )
    state = gate.build_authority_state(("source_boundary",))
    assert state["all_checks_passed"] is False and state["authority_rows"] == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("symlink", True),
        ("regular_file", False),
        ("tracked", False),
        ("sha256_observed", "0" * 64),
        ("source_check_passed", False),
    ],
)
def test_frozen_csv_reader_refuses_boundary_failures_without_parser_call(
    monkeypatch: pytest.MonkeyPatch, field: str, value: object,
) -> None:
    relative = gate.HISTORICAL_AVAILABILITY_SOURCE_PATH
    row = copy.deepcopy(next(
        item for item in gate._source_rows()
        if item["source_relative_path"] == str(relative)
    ))
    row[field] = value
    monkeypatch.setattr(
        gate, "_read_csv_document",
        lambda _path: (_ for _ in ()).throw(AssertionError("low-level parser called")),
    )
    document = gate._read_frozen_csv_document(relative, {str(relative): row})
    assert document == gate.CsvDocument((), (), "blocked", "SOURCE_ACCESS_NOT_ALLOWED")


def test_frozen_json_reader_refuses_hash_drift_without_read_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    relative = gate.P6A_ROOT / gate.P6A_FILENAMES[-1]
    row = copy.deepcopy(next(
        item for item in gate._source_rows()
        if item["source_relative_path"] == str(relative)
    ))
    row["sha256_observed"] = "0" * 64
    original = Path.read_text
    called = False

    def guarded_read_text(path: Path, *args, **kwargs):
        nonlocal called
        if path == gate.REPO_ROOT / relative:
            called = True
            raise AssertionError("frozen JSON content read")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    document = gate._read_frozen_json(relative, {str(relative): row})
    assert document == gate.JsonDocument({}, "blocked", "SOURCE_ACCESS_NOT_ALLOWED")
    assert called is False


def test_tmp_metadata_symlink_target_sentinel_is_not_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    relative = Path("metadata/source.csv")
    target = tmp_path / "sentinel.csv"
    sentinel = "SENTINEL_MUST_NOT_BE_READ"
    target.write_text(sentinel, encoding="utf-8")
    source = tmp_path / relative
    source.parent.mkdir(parents=True)
    source.symlink_to(target)
    expected = hashlib.sha256(sentinel.encode()).hexdigest()
    monkeypatch.setattr(gate, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(gate, "SOURCE_PATHS", (relative,))
    monkeypatch.setattr(gate, "SOURCE_SHA256", {str(relative): expected})
    parser_called = False

    def forbidden_parser(_path: Path):
        nonlocal parser_called
        parser_called = True
        raise AssertionError("symlink target parser called")

    monkeypatch.setattr(gate, "_read_csv_document", forbidden_parser)
    row = {
        "source_relative_path": str(relative),
        "tracked": True,
        "regular_file": False,
        "symlink": True,
        "source_check_passed": False,
        "sha256_expected": expected,
        "sha256_observed": "",
    }
    document = gate._read_frozen_csv_document(relative, {str(relative): row})
    assert document.blocking_reason == "SOURCE_ACCESS_NOT_ALLOWED"
    assert parser_called is False
    assert target.read_text(encoding="utf-8") == sentinel


def test_three_exact_headers_and_roles() -> None:
    documents = _documents()
    assert documents["availability"].header == gate.AVAILABILITY_HEADER
    assert documents["integrity"].header == gate.INTEGRITY_HEADER
    assert documents["independence"].header == gate.INDEPENDENCE_HEADER
    assert all(gate._source_role_checks(documents).values())


@pytest.mark.parametrize("mutation", ["missing", "reorder", "duplicate", "extra"])
def test_header_schema_drift_fails_role_contract(mutation: str) -> None:
    documents = _documents()
    document = documents["availability"]
    header = list(document.header)
    if mutation == "missing": header.pop()
    elif mutation == "reorder": header[0], header[1] = header[1], header[0]
    elif mutation == "duplicate": header[1] = header[0]
    else: header.append("extra")
    documents["availability"] = gate.CsvDocument(tuple(header), document.rows, "passed", "")
    assert not all(gate._source_role_checks(documents).values())


@pytest.mark.parametrize("content,reason", [("", "CSV_HEADER_MISSING"), ("a,b\n", "CSV_DATA_ROWS_EMPTY"), ("a,a\n1,2\n", "CSV_HEADER_DUPLICATE"), ("a,b\n1,2,3\n", "CSV_ROW_HEADER_MISMATCH")])
def test_structured_reader_fails_closed_without_indexerror(tmp_path: Path, content: str, reason: str) -> None:
    path = tmp_path / "input.csv"
    path.write_text(content, encoding="utf-8")
    document = gate._read_csv_document(path)
    assert document.status == "blocked" and document.blocking_reason == reason


def test_source_role_swap_fails() -> None:
    documents = _documents()
    documents["availability"], documents["integrity"] = documents["integrity"], documents["availability"]
    assert not all(gate._source_role_checks(documents).values())


@pytest.mark.parametrize("value", ["true", "TRUE", "1", " True", True])
def test_exact_true_semantics_reject_variants(value: object) -> None:
    assert not gate._csv_true(value)


@pytest.mark.parametrize("value", ["false", "FALSE", "0", "False ", False])
def test_exact_false_semantics_reject_variants(value: object) -> None:
    assert not gate._csv_false(value)


@pytest.mark.parametrize("role,field,value", [
    ("availability", "raw_file_available", "true"),
    ("availability", "git_tracked", "false"),
    ("availability", "ready_for_training_current_step", "FALSE"),
    ("integrity", "starts_with_data_block", "true"),
    ("integrity", "first_nonempty_line", "data_WRONG"),
    ("integrity", "qa_comment", "wrong"),
    ("independence", "source_stage", "expansion"),
    ("independence", "raw_sha256_unchanged", "true"),
    ("independence", "blocking_reasons", "blocked"),
])
def test_exact_source_status_failures_have_precise_reason(role: str, field: str, value: str) -> None:
    documents = _mutate_target(_documents(), role, "6BV6", field, value)
    rows = gate._authority_rows(_binding_document(), documents)
    assert rows[0]["blocking_reason"] == "HISTORICAL_AUTHORITY_SOURCE_STATUS_FAILED"


def test_p6a_predecessor_all_explicit_checks_pass() -> None:
    checks = gate._p6a_checks()
    assert len(checks) >= 30 and all(checks.values())


@pytest.mark.parametrize("field,value", [("all_checks_passed", False), ("real_sample_binding_count", 12), ("ready_for_training", True), ("integration_architecture", "wrong")])
def test_p6a_manifest_drift_fails(field: str, value: Any) -> None:
    manifest, document = gate._p6a_inputs()
    changed = copy.deepcopy(manifest)
    changed[field] = value
    assert not all(gate._p6a_checks(changed, document).values())


@pytest.mark.parametrize("mutation", ["shape", "order", "identity", "path"])
def test_p6a_binding_drift_fails(mutation: str) -> None:
    manifest, document = gate._p6a_inputs()
    rows = [dict(row) for row in document.rows]
    if mutation == "shape": rows.pop()
    elif mutation == "order": rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "identity": rows[0]["pdb_id"] = "WRONG"
    else: rows[0]["raw_target_relative_path"] = "data/raw/covalent_sources/wrong.cif"
    changed = gate.CsvDocument(document.header, tuple(rows), "passed", "")
    assert not all(gate._p6a_checks(manifest, changed).values())


def test_authority_exact_three_by_twenty_five_and_provenance_roles() -> None:
    rows = gate._authority_rows()
    assert gate.validate_authority_rows(rows)
    assert len(rows) == 3 and all(len(row) == 25 for row in rows)
    assert all(row["expected_sha256"] == row["prior_observed_sha256"] == row["independence_sha256_before"] == row["independence_sha256_after"] for row in rows)
    assert [row["availability_source_row_id"] for row in rows] == ["AVAILABILITY_ROW_000002", "AVAILABILITY_ROW_000004", "AVAILABILITY_ROW_000005"]
    assert [row["integrity_source_row_id"] for row in rows] == ["INTEGRITY_ROW_000002", "INTEGRITY_ROW_000004", "INTEGRITY_ROW_000005"]


@pytest.mark.parametrize("mutation", ["integrity_pdb", "integrity_path", "integrity_duplicate", "integrity_missing", "other_pdb_same_path"])
def test_integrity_pdb_and_path_join_fail_closed(mutation: str) -> None:
    documents = _documents()
    rows = [dict(row) for row in documents["integrity"].rows]
    target = next(index for index, row in enumerate(rows) if row["pdb_id"] == "6BV6")
    if mutation == "integrity_pdb": rows[target]["pdb_id"] = "WRONG"
    elif mutation == "integrity_path": rows[target]["raw_path"] = "data/raw/covalent_sources/wrong.cif"
    elif mutation == "integrity_duplicate": rows.insert(target, dict(rows[target]))
    elif mutation == "integrity_missing": rows.pop(target)
    else:
        rows[target]["pdb_id"] = "6BV9"
    documents = _replace_rows(documents, "integrity", rows)
    authority = gate._authority_rows(_binding_document(), documents)
    assert authority[0]["authority_status"] == "blocked"
    assert authority[0]["blocking_reason"] == "HISTORICAL_AUTHORITY_SOURCE_JOIN_NOT_ONE_TO_ONE"


@pytest.mark.parametrize("role,field,value,reason", [
    ("availability", "expected_het_id", "BAD", "HISTORICAL_AUTHORITY_IDENTITY_MISMATCH"),
    ("independence", "ligand_comp_id", "BAD", "HISTORICAL_AUTHORITY_IDENTITY_MISMATCH"),
    ("availability", "raw_path", "data/raw/covalent_sources/wrong.cif", "HISTORICAL_AUTHORITY_RAW_PATH_MISMATCH"),
    ("independence", "raw_source_path", "data/raw/covalent_sources/wrong.cif", "HISTORICAL_AUTHORITY_RAW_PATH_MISMATCH"),
    ("availability", "raw_file_sha256", "x", "HISTORICAL_AUTHORITY_INVALID_HASH"),
    ("availability", "raw_file_sha256", "0" * 64, "HISTORICAL_AUTHORITY_HASH_MISMATCH"),
    ("independence", "raw_sha256_after", "0" * 64, "HISTORICAL_AUTHORITY_HASH_MISMATCH"),
    ("availability", "raw_file_size_bytes", "0", "HISTORICAL_AUTHORITY_INVALID_SIZE"),
    ("availability", "raw_file_size_bytes", "1", "HISTORICAL_AUTHORITY_SIZE_MISMATCH"),
])
def test_authority_conflicts_have_deterministic_reasons(role: str, field: str, value: str, reason: str) -> None:
    documents = _mutate_target(_documents(), role, "6BV6", field, value)
    authority = gate._authority_rows(_binding_document(), documents)
    assert authority[0]["blocking_reason"] == reason
    assert authority[0]["authority_status"] == "blocked"


@pytest.mark.parametrize("role", ["availability", "integrity", "independence"])
@pytest.mark.parametrize("mutation", ["missing", "duplicate"])
def test_missing_or_duplicate_target_source_row_fails(role: str, mutation: str) -> None:
    documents = _documents()
    rows = [dict(row) for row in documents[role].rows]
    index = next(i for i, row in enumerate(rows) if row["pdb_id"] == "6BV6")
    if mutation == "missing": rows.pop(index)
    else: rows.insert(index, dict(rows[index]))
    documents = _replace_rows(documents, role, rows)
    authority = gate._authority_rows(_binding_document(), documents)
    assert authority[0]["blocking_reason"] == "HISTORICAL_AUTHORITY_SOURCE_JOIN_NOT_ONE_TO_ONE"


def test_unsafe_joined_path_fails_with_precise_reason() -> None:
    unsafe = "data/raw/covalent_sources/file.CIF"
    binding = _binding_document()
    binding_rows = [dict(row) for row in binding.rows]
    binding_rows[0]["raw_target_relative_path"] = unsafe
    binding = gate.CsvDocument(binding.header, tuple(binding_rows), "passed", "")
    documents = _documents()
    documents = _mutate_target(documents, "availability", "6BV6", "raw_path", unsafe)
    documents = _mutate_target(documents, "integrity", "6BV6", "raw_path", unsafe)
    documents = _mutate_target(documents, "independence", "6BV6", "raw_source_path", unsafe)
    authority = gate._authority_rows(binding, documents)
    assert authority[0]["blocking_reason"] == "HISTORICAL_AUTHORITY_UNSAFE_RAW_PATH"


def test_correct_count_wrong_identity_set_fails_validator() -> None:
    rows = copy.deepcopy(gate._authority_rows())
    rows[0]["pdb_id"] = "WRONG"
    assert not gate.validate_authority_rows(rows)


def test_grounded_locator_tracks_source_reorder() -> None:
    documents = _documents()
    before = gate._authority_rows(_binding_document(), documents)[0]["availability_source_row_id"]
    availability = [dict(row) for row in documents["availability"].rows]
    availability[0], availability[1] = availability[1], availability[0]
    serialized_before = json.dumps(list(documents["availability"].rows), sort_keys=True)
    documents = _replace_rows(documents, "availability", availability)
    serialized_after = json.dumps(list(documents["availability"].rows), sort_keys=True)
    after = gate._authority_rows(_binding_document(), documents)[0]["availability_source_row_id"]
    assert before == "AVAILABILITY_ROW_000002" and after == "AVAILABILITY_ROW_000001"
    assert hashlib.sha256(serialized_before.encode()).hexdigest() != hashlib.sha256(serialized_after.encode()).hexdigest()


class StringSubclass(str):
    pass


@pytest.mark.parametrize("value", [None, "", " data/raw/covalent_sources/a.cif", "data/raw/covalent_sources/a.cif ", "data\\raw\\a.cif", "data/raw/covalent_sources/a\x00.cif", "/data/raw/covalent_sources/a.cif", "https://x/a.cif", "C:/a.cif", "data//raw/a.cif", "data/./raw/a.cif", "data/raw/../a.cif", "data/raw/?/a.cif", "data/derived/a.cif", "data/raw/covalent_sources/a.pdb", "data/raw/covalent_sources/a.CIF", StringSubclass("data/raw/covalent_sources/a.cif")])
def test_path_helper_rejects_unsafe_values(value: object) -> None:
    assert gate._safe_raw_target_relative_path(value) is False
    assert gate._safe_raw_target_relative_path(value) == p6a._safe_raw_target_relative_path(value)


@pytest.mark.parametrize("value", [*gate.HISTORICAL_RAW_PATHS, "data/raw/covalent_sources/a.mmcif"])
def test_path_helper_parity_with_p6a(value: object) -> None:
    assert gate._safe_raw_target_relative_path(value) == p6a._safe_raw_target_relative_path(value)


def test_contract_is_48_rows_evidence_driven_and_exact() -> None:
    state = gate.build_authority_state()
    assert gate.validate_contract_rows(state["contract_rows"], state["contract_observations"])
    assert len(state["contract_rows"]) == 48
    assert all(row["contract_passed"] for row in state["contract_rows"])
    assert len({row["observed_value"] for row in state["contract_rows"]}) > 4


@pytest.mark.parametrize("mutation", ["empty", "reorder", "coordinated_drift"])
def test_contract_validator_rejects_drift(mutation: str) -> None:
    state = gate.build_authority_state()
    rows = copy.deepcopy(state["contract_rows"])
    if mutation == "empty": rows = []
    elif mutation == "reorder": rows[0], rows[1] = rows[1], rows[0]
    else:
        rows[0]["expected_value"] = rows[0]["observed_value"] = "drift"
    assert not gate.validate_contract_rows(rows, state["contract_observations"])


def test_validator_helper_failure_propagates_to_contract() -> None:
    state = gate.build_authority_state()
    observations = dict(state["contract_observations"])
    observations["invalid_hash_rejected"] = "false"
    rows = gate._contract_rows(observations)
    assert not all(row["contract_passed"] for row in rows)


@pytest.mark.parametrize("name,builder,validator", [
    ("issues", gate._issue_rows, gate.validate_issue_rows),
    ("safety", gate._safety_rows, gate.validate_safety_rows),
])
def test_issue_and_safety_validators_are_full_equality(name: str, builder, validator) -> None:
    rows = builder()
    assert validator(rows)
    assert not validator([])
    drift = copy.deepcopy(rows)
    drift[0][next(key for key in drift[0] if key.endswith("status"))] = "drift"
    assert not validator(drift), name


def test_no_issues_substitution_fails() -> None:
    issues = gate._issue_rows()
    issues[0]["issue_id"] = "NO_ISSUES"
    assert not gate.validate_issue_rows(issues)


@pytest.mark.parametrize("section", gate.SECTION_NAMES)
def test_each_section_forced_failure_materializes_false_manifest(tmp_path: Path, section: str) -> None:
    root = _materialize(tmp_path, (section,))
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest["all_checks_passed"] is False
    assert manifest["historical_raw_fingerprint_authority_consolidation_passed"] is False
    assert manifest["historical_single_authority_file_materialized"] is False
    assert manifest["ready_for_real_raw_source_precondition_gate"] is False
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP
    assert len(manifest["current_domain_blocking_reasons"]) == 10
    assert len(manifest["authority_followup_issue_ids"]) == 3
    assert manifest[f"all_{section}_checks_passed" if section not in {"p6a_predecessor", "source_role_contract", "authority_rows", "authority_contract"} else {"p6a_predecessor": "all_p6a_predecessor_checks_passed", "source_role_contract": "all_source_role_contract_checks_passed", "authority_rows": "all_authority_row_checks_passed", "authority_contract": "all_authority_contract_checks_passed"}[section]] is False


def test_source_boundary_false_manifest_has_no_authority_overclaim(tmp_path: Path) -> None:
    root = _materialize(tmp_path, ("source_boundary",))
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest["all_source_boundary_checks_passed"] is False
    assert manifest["all_p6a_predecessor_checks_passed"] is False
    assert manifest["all_source_role_contract_checks_passed"] is False
    assert manifest["all_authority_row_checks_passed"] is False
    assert manifest["all_authority_contract_checks_passed"] is False
    assert manifest["all_checks_passed"] is False
    assert manifest["p6a_design_frozen"] is False
    assert manifest["source_role_contract_frozen"] is False
    assert manifest["historical_single_authority_file_materialized"] is False
    assert manifest["historical_raw_fingerprint_authority_consolidation_passed"] is False
    assert manifest["ready_for_real_raw_source_precondition_gate"] is False
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP
    assert manifest["authority_passed_count"] == 0
    assert manifest["historical_authority_row_count"] == 0
    assert len(manifest["current_domain_blocking_reasons"]) == 10
    assert len(manifest["authority_followup_issue_ids"]) == 3


def test_checker_runtime_boundary_failure_does_not_read_sources(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    checker = _load_checker()
    root = _materialize(tmp_path)
    rows = copy.deepcopy(gate._source_rows())
    rows[-1]["symlink"] = True
    rows[-1]["regular_file"] = False
    rows[-1]["source_check_passed"] = False
    monkeypatch.setattr(gate, "_source_rows", lambda: rows)
    monkeypatch.setattr(
        gate, "_p6a_inputs",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("P6-A source read")),
    )
    monkeypatch.setattr(
        gate, "_historical_documents",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("historical source read")),
    )
    with pytest.raises(AssertionError):
        checker.validate_materialized_outputs(root)


def test_unknown_or_duplicate_forced_section_rejected() -> None:
    with pytest.raises(ValueError): gate.build_authority_state(("unknown",))
    with pytest.raises(ValueError): gate.build_authority_state(("safety", "safety"))


@pytest.mark.parametrize("filename", gate.CSV_OUTPUTS)
def test_checker_rejects_each_csv_disk_drift(tmp_path: Path, filename: str) -> None:
    checker = _load_checker()
    root = _materialize(tmp_path)
    path = root / filename
    path.write_text(path.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
    with pytest.raises(AssertionError): checker.validate_materialized_outputs(root)


@pytest.mark.parametrize("mutation", ["missing", "extra", "symlink"])
def test_checker_rejects_output_set_drift(tmp_path: Path, mutation: str) -> None:
    checker = _load_checker()
    root = _materialize(tmp_path)
    if mutation == "missing": (root / gate.ISSUE_FILENAME).unlink()
    elif mutation == "extra": (root / "extra.csv").write_text("x\n", encoding="utf-8")
    else:
        path = root / gate.ISSUE_FILENAME
        path.unlink(); path.symlink_to(root / gate.CONTRACT_FILENAME)
    with pytest.raises(AssertionError): checker.validate_materialized_outputs(root)


def test_checker_rejects_first_hash_drift(tmp_path: Path) -> None:
    checker = _load_checker()
    root = _materialize(tmp_path)
    first = _hashes(root)
    path = root / gate.CONTRACT_FILENAME
    path.write_text(path.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
    with pytest.raises(AssertionError): checker.validate_materialized_outputs(root, first)


def test_checker_rejects_manifest_overclaim(tmp_path: Path) -> None:
    checker = _load_checker()
    root = _materialize(tmp_path, ("safety",))
    path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["all_checks_passed"] = True
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError): checker.validate_materialized_outputs(root)


def test_checker_direct_rows_reject_drift_even_with_synchronized_output_hash(tmp_path: Path) -> None:
    checker = _load_checker()
    root = _materialize(tmp_path)
    contract_path = root / gate.CONTRACT_FILENAME
    text = contract_path.read_text(encoding="utf-8").replace("P6-A predecessor stage and state", "coordinated drift", 1)
    contract_path.write_text(text, encoding="utf-8")
    manifest_path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_sha256"][gate.CONTRACT_FILENAME] = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError): checker.validate_materialized_outputs(root)


def test_checker_rejects_source_sha_constant_drift(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    checker = _load_checker()
    root = _materialize(tmp_path)
    changed = dict(gate.SOURCE_SHA256)
    changed[str(gate.SOURCE_PATHS[0])] = "0" * 64
    monkeypatch.setattr(gate, "SOURCE_SHA256", changed)
    with pytest.raises(AssertionError): checker.validate_materialized_outputs(root)


def test_checker_canonical_validated_source_snapshot() -> None:
    checker = _load_checker()
    snapshot = checker._validated_source_hash_snapshot()
    assert snapshot == gate.SOURCE_SHA256
    assert tuple(snapshot) == tuple(str(path) for path in gate.SOURCE_PATHS)


@pytest.mark.parametrize(
    "mutation",
    [
        "symlink", "nonregular", "untracked", "check_failed", "hash_drift",
        "missing", "reorder", "extra",
    ],
)
def test_checker_source_snapshot_rejects_boundary_drift(
    monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    checker = _load_checker()
    rows = copy.deepcopy(gate._source_rows())
    if mutation == "symlink":
        rows[0]["symlink"] = True
    elif mutation == "nonregular":
        rows[0]["regular_file"] = False
    elif mutation == "untracked":
        rows[0]["tracked"] = False
    elif mutation == "check_failed":
        rows[0]["source_check_passed"] = False
    elif mutation == "hash_drift":
        rows[0]["sha256_observed"] = "0" * 64
    elif mutation == "missing":
        rows.pop()
    elif mutation == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    else:
        rows.append(copy.deepcopy(rows[-1]))
    monkeypatch.setattr(gate, "_source_rows", lambda: rows)
    with pytest.raises(AssertionError):
        checker._validated_source_hash_snapshot()


def test_checker_source_snapshot_never_calls_checker_sha256(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    monkeypatch.setattr(
        checker, "_sha256",
        lambda _path: (_ for _ in ()).throw(AssertionError("checker direct hash")),
    )
    assert checker._validated_source_hash_snapshot() == gate.SOURCE_SHA256


def test_checker_has_no_direct_source_paths_filesystem_hash_loop() -> None:
    source = CHECK_PATH.read_text(encoding="utf-8")
    assert "_sha256(REPO_ROOT / path)" not in source
    assert "(REPO_ROOT / path).read_bytes" not in source
    assert "(REPO_ROOT / path).read_text" not in source
    assert "open(REPO_ROOT / path" not in source
    assert "(REPO_ROOT / path).stat" not in source
    assert "(REPO_ROOT / path).lstat" not in source
    assert "(REPO_ROOT / path).resolve" not in source


def test_checker_snapshot_symlink_sentinel_not_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    checker = _load_checker()
    target = tmp_path / "sentinel.csv"
    sentinel = "CHECKER_MUST_NOT_READ_THIS_SENTINEL"
    target.write_text(sentinel, encoding="utf-8")
    source = tmp_path / "source.csv"
    source.symlink_to(target)
    rows = copy.deepcopy(gate._source_rows())
    rows[0]["regular_file"] = False
    rows[0]["symlink"] = True
    rows[0]["source_check_passed"] = False
    rows[0]["sha256_observed"] = ""
    checker_sha_called = False

    def forbidden_hash(_path: Path):
        nonlocal checker_sha_called
        checker_sha_called = True
        raise AssertionError("checker direct filesystem hash")

    monkeypatch.setattr(gate, "_source_rows", lambda: rows)
    monkeypatch.setattr(checker, "_sha256", forbidden_hash)
    with pytest.raises(AssertionError):
        checker._validated_source_hash_snapshot()
    assert checker_sha_called is False
    assert target.read_text(encoding="utf-8") == sentinel


def test_checker_main_stops_before_materialization_when_snapshot_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    materialization_called = False

    def boundary_failure():
        raise AssertionError("SOURCE_SNAPSHOT_BOUNDARY_FAILED")

    def forbidden_materialization(*_args, **_kwargs):
        nonlocal materialization_called
        materialization_called = True
        raise RuntimeError("MATERIALIZATION_MUST_NOT_START")

    monkeypatch.setattr(checker, "_validated_source_hash_snapshot", boundary_failure)
    monkeypatch.setattr(
        gate,
        "run_covapie_bulk_download_admission_covalent_residue_locator_historical_raw_fingerprint_authority_consolidation_gate_v1",
        forbidden_materialization,
    )
    with pytest.raises(AssertionError, match="SOURCE_SNAPSHOT_BOUNDARY_FAILED"):
        checker.main()
    assert materialization_called is False


def test_checker_rejects_runtime_source_role_drift(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    checker = _load_checker()
    root = _materialize(tmp_path)
    documents = _documents()
    documents["availability"], documents["integrity"] = documents["integrity"], documents["availability"]
    monkeypatch.setattr(gate, "_historical_documents", lambda *_args, **_kwargs: documents)
    with pytest.raises(AssertionError): checker.validate_materialized_outputs(root)


def test_production_has_no_raw_access_or_traversal_code() -> None:
    text = MODULE_PATH.read_text(encoding="utf-8")
    for forbidden in ("os.walk", ".rglob(", ".glob(", ".stat("):
        assert forbidden not in text
    assert "absolute.lstat()" in text
