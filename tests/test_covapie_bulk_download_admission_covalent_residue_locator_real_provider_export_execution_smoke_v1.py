"""Targeted success and fail-closed tests for Step14AU-E0-P6-C."""

from __future__ import annotations

import copy
import builtins
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import fields, replace
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke
    as gate,
)


CHECK_PATH = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1.py"
EXPECTED_OUTPUT_SHA256 = {
    gate.CONTRACT_FILENAME: "82f3f225cb2e18ba19ff386e612670279ebcdf4a0435b7b4642ff8167ccb09b7",
    gate.SIDECAR_FILENAME: "066c0beeaa01d31a6d6ea3fae62f3df5177c2d904f6295646ee33a7fcd780ac7",
    gate.EVIDENCE_FILENAME: "4048efdfe373fe955995ded43639fcbd7baf67560e867662dbd18fe22a4fb1ab",
    gate.SAFETY_FILENAME: "e7736e3567d6ef76d19b13f46741f297000ea130644dd8b8b4b653b9a04bc6dc",
    gate.ISSUE_FILENAME: "5bda40b683d649fb28a2172291f329c1f87d10f3a2bd122e1d5a6ab887a071c4",
    gate.MANIFEST_FILENAME: "9061e36c333cf498dd5844407f5df11d64c3e271ae47e407938d34ac851d3aab",
}


def _modules():
    return gate._load_runtime_modules()


@pytest.fixture(scope="module")
def real_state():
    state = gate.build_execution_state()
    assert state["all_checks_passed"] is True
    return state


def _load_checker():
    spec = importlib.util.spec_from_file_location("p6c_checker", CHECK_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _quote(value: str) -> str:
    if value == "":
        return "''"
    if any(character.isspace() for character in value):
        return "'" + value.replace("'", "\\'") + "'"
    return value


def _binding(**changes: str) -> dict[str, str]:
    values = {
        "binding_row_id": "REAL_LOCATOR_BINDING_000001",
        "source_pipeline": "synthetic_test",
        "sample_preparation_input_id": "SAMPLE_TEST_001",
        "sample_execution_id": "EXEC_TEST_001",
        "pdb_id": "TEST",
        "ligand_comp_id": "LIG",
        "conn_id": "CONN1",
        "covalent_residue_name": "CYS",
        "selected_residue_chain_id": "A",
        "selected_residue_index": "25",
        "selected_residue_atom_name": "SG",
        "raw_target_relative_path": "data/raw/covalent_sources/synthetic/test.cif",
        "expected_raw_sha256": "",
        "expected_raw_size_bytes": "0",
    }
    values.update(changes)
    return values


STRUCT_TAGS = (
    "_struct_conn.id", "_struct_conn.conn_type_id",
    "_struct_conn.ptnr1_label_comp_id", "_struct_conn.ptnr1_auth_comp_id",
    "_struct_conn.ptnr1_label_atom_id", "_struct_conn.ptnr1_auth_atom_id",
    "_struct_conn.ptnr1_auth_asym_id", "_struct_conn.ptnr1_auth_seq_id",
    "_struct_conn.ptnr1_label_asym_id", "_struct_conn.ptnr1_label_seq_id",
    "_struct_conn.pdbx_ptnr1_PDB_ins_code",
    "_struct_conn.ptnr2_label_comp_id", "_struct_conn.ptnr2_auth_comp_id",
    "_struct_conn.ptnr2_label_atom_id", "_struct_conn.ptnr2_auth_atom_id",
    "_struct_conn.ptnr2_auth_asym_id", "_struct_conn.ptnr2_auth_seq_id",
    "_struct_conn.ptnr2_label_asym_id", "_struct_conn.ptnr2_label_seq_id",
    "_struct_conn.pdbx_ptnr2_PDB_ins_code",
)
ATOM_TAGS = (
    "_atom_site.id", "_atom_site.label_comp_id", "_atom_site.auth_comp_id",
    "_atom_site.label_atom_id", "_atom_site.auth_atom_id",
    "_atom_site.auth_asym_id", "_atom_site.auth_seq_id",
    "_atom_site.label_asym_id", "_atom_site.label_seq_id",
    "_atom_site.pdbx_PDB_ins_code",
)


def _synthetic_mmcif(
    *,
    struct_rows: list[list[str]] | None = None,
    atom_rows: list[list[str]] | None = None,
    struct_insertion: str = "?",
    atom_insertion: str = "?",
    include_struct_insertion: bool = True,
    include_atom_insertion: bool = True,
) -> bytes:
    default_struct = [
        "CONN1", "covale", "CYS", "CYS", "SG", "SG", "A", "25", "A", "25",
        struct_insertion, "LIG", "LIG", "C2", "C2", "B", "1", "B", "1", ".",
    ]
    default_atom = ["101", "CYS", "CYS", "SG", "SG", "A", "25", "A", "25", atom_insertion]
    s_tags = list(STRUCT_TAGS)
    a_tags = list(ATOM_TAGS)
    s_rows = copy.deepcopy(struct_rows if struct_rows is not None else [default_struct])
    a_rows = copy.deepcopy(atom_rows if atom_rows is not None else [default_atom])
    if not include_struct_insertion:
        index = s_tags.index("_struct_conn.pdbx_ptnr1_PDB_ins_code")
        s_tags.pop(index)
        for row in s_rows:
            row.pop(index)
        index = s_tags.index("_struct_conn.pdbx_ptnr2_PDB_ins_code")
        s_tags.pop(index)
        for row in s_rows:
            row.pop(index)
    if not include_atom_insertion:
        index = a_tags.index("_atom_site.pdbx_PDB_ins_code")
        a_tags.pop(index)
        for row in a_rows:
            row.pop(index)
    lines = ["data_test", "loop_", *s_tags]
    lines.extend(" ".join(_quote(value) for value in row) for row in s_rows)
    lines.extend(["#", "loop_", *a_tags])
    lines.extend(" ".join(_quote(value) for value in row) for row in a_rows)
    lines.append("#")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _verified(payload: bytes, relative: str) -> gate.VerifiedRawSource:
    digest = hashlib.sha256(payload).hexdigest()
    return gate.VerifiedRawSource(
        relative, payload, digest, digest, len(payload), len(payload),
        (1, 2, 3, 4, len(payload), 5, 6),
        (1, 2, 3, 4, len(payload), 5, 6), True, "",
    )


def _execute(
    payload: bytes,
    *,
    binding: dict[str, str] | None = None,
    p4=None,
    p5b=None,
):
    p4_real, p5b_real = _modules()
    selected_binding = dict(binding or _binding())
    digest = hashlib.sha256(payload).hexdigest()
    selected_binding["expected_raw_sha256"] = digest
    selected_binding["expected_raw_size_bytes"] = str(len(payload))
    verified = _verified(payload, selected_binding["raw_target_relative_path"])
    return gate.execute_one_binding(
        selected_binding, 1, p4=p4 or p4_real, p5b=p5b or p5b_real,
        raw_reader=lambda *args, **kwargs: verified,
    )


def _raw_fixture(root: Path, payload: bytes = b"same retained bytes\n") -> tuple[str, Path, str]:
    relative = "data/raw/covalent_sources/synthetic/sample.cif"
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return relative, path, hashlib.sha256(payload).hexdigest()


def test_fixed_source_schema_and_execution_api() -> None:
    assert gate.STEP_LABEL == "Step14AU-E0-P6-C"
    assert len(gate.SOURCE_PATHS) == len(gate.SOURCE_SHA256) == 11
    assert tuple(gate.SOURCE_SHA256) == gate.SOURCE_PATHS
    assert len(gate.FUTURE_REAL_SIDECAR_COLUMNS) == 41
    assert len(gate.EVIDENCE_COLUMNS) == 25
    assert len(gate.OUTPUT_FILES) == 6
    assert tuple(field.name for field in fields(gate.VerifiedRawSource)) == (
        "relative_path", "content_bytes", "expected_sha256", "observed_sha256",
        "expected_size_bytes", "observed_size_bytes", "pre_stat_fingerprint",
        "post_stat_fingerprint", "passed", "blocking_reason",
    )


def test_runtime_loader_requests_only_p4_and_p5b(monkeypatch) -> None:
    requested: list[str] = []

    def import_only_allowed(name: str):
        assert name not in gate.FORBIDDEN_RUNTIME_MODULE_NAMES
        requested.append(name)
        return ModuleType(name)

    monkeypatch.setattr(gate.importlib, "import_module", import_only_allowed)
    p4, p5b = gate._load_runtime_modules()
    assert requested == [gate.P4_RUNTIME_MODULE_NAME, gate.P5B_RUNTIME_MODULE_NAME]
    assert (p4.__name__, p5b.__name__) == tuple(requested)


def test_frozen_p6a_p6b_schemas_are_statically_extracted() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    passed, schemas = gate._extract_frozen_schema_contract(snapshot)
    assert passed is True
    assert schemas == {
        "p6a_future_real_sidecar_columns": gate.FUTURE_REAL_SIDECAR_COLUMNS,
        "p6a_binding_columns": gate.P6A_BINDING_COLUMNS,
        "p6b_matrix_columns": gate.P6B_MATRIX_COLUMNS,
    }


def test_schema_extraction_does_not_exec_eval_or_import(monkeypatch) -> None:
    source = b"""
BASE = ('alpha', 'beta')
TARGET = (*BASE, 'gamma')
import module_that_must_not_be_imported
raise RuntimeError('module body must not execute')
"""

    def forbidden(*args, **kwargs):
        pytest.fail("schema extraction attempted runtime evaluation")

    monkeypatch.setattr(builtins, "exec", forbidden)
    monkeypatch.setattr(builtins, "eval", forbidden)
    monkeypatch.setattr(builtins, "__import__", forbidden)
    assert gate._extract_literal_tuple_assignment(source, "TARGET") == (
        "alpha", "beta", "gamma",
    )


@pytest.mark.parametrize(
    "source",
    [
        b"OTHER = ('a',)\n",
        b"TARGET = ('a',)\nTARGET = ('b',)\n",
        b"TARGET = build_schema()\n",
        b"TARGET = ('a', 1)\n",
        b"TARGET = ()\n",
        b"TARGET = ('a', 'a')\n",
        b"TARGET = (*UNKNOWN, 'a')\n",
    ],
)
def test_schema_extraction_fails_closed(source: bytes) -> None:
    assert gate._extract_literal_tuple_assignment(source, "TARGET") == ()


def test_p6a_metadata_csvs_are_not_read_and_p6_modules_are_not_imported(
    monkeypatch,
) -> None:
    forbidden_filenames = {
        "covapie_sample_preparation_execution_manifest.csv",
        "sample_index.csv",
        "covapie_batch_sample_preparation_execution_manifest.csv",
    }
    forbidden_reads: list[Path] = []
    original_open = Path.open

    def guarded_open(path: Path, *args, **kwargs):
        if path.name in forbidden_filenames:
            forbidden_reads.append(path)
            pytest.fail(f"undeclared P6-A metadata read: {path}")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    for name in gate.FORBIDDEN_RUNTIME_MODULE_NAMES:
        sys.modules.pop(name, None)
    state = gate.build_execution_state()
    assert state["schema_ok"] is True
    assert state["runtime_modules_ok"] is True
    assert state["runtime_module_names"] == (
        gate.P4_RUNTIME_MODULE_NAME, gate.P5B_RUNTIME_MODULE_NAME,
    )
    assert state["all_checks_passed"] is True
    assert forbidden_reads == []
    assert all(name not in sys.modules for name in gate.FORBIDDEN_RUNTIME_MODULE_NAMES)


def test_schema_failure_prevents_runtime_modules_raw_parser_and_provider() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    raw_calls: list[object] = []
    state = gate.build_execution_state(
        source_snapshot=snapshot,
        schema_validator=lambda frozen: (False, {}),
        module_loader=lambda: pytest.fail("runtime module import"),
        raw_reader=lambda *args, **kwargs: raw_calls.append(args) or pytest.fail("raw access"),
    )
    assert state["schema_ok"] is False
    assert state["runtime_modules_ok"] is False
    assert state["modules_ok"] is False
    assert state["counters"] == {
        "raw": 0, "decode": 0, "struct_parse": 0, "atom_parse": 0,
        "provider": 0,
    }
    assert raw_calls == [] and state["sidecar_rows"] == []
    assert state["all_checks_passed"] is False
    manifest = gate._manifest_payload(state, {})
    assert manifest["real_provider_export_execution_smoke_passed"] is False
    assert manifest["ready_for_real_provider_sidecar_integration"] is False
    assert manifest["insertion_code_provenance_export_ready_for_real_samples"] is False


def test_source_boundary_and_p6b_predecessor_are_directly_validated() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert tuple(record.sha256 for record in snapshot.records) == tuple(
        gate.SOURCE_SHA256[path] for path in gate.SOURCE_PATHS
    )
    passed, bindings, matrix, manifest = gate._validate_p6b_predecessor(snapshot)
    assert passed and len(bindings) == len(matrix) == 11
    assert manifest["all_checks_passed"] is True
    assert manifest["ready_for_real_provider_export_execution_smoke"] is True
    assert manifest["ready_for_real_provider_export_execution"] is False
    assert manifest["p5b_parser_called_current_step"] is False
    assert manifest["p4_provider_called_current_step"] is False
    assert len(gate._join_bindings_and_preconditions(bindings, matrix)) == 11


def test_source_failure_prevents_module_load_and_all_raw_access() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    blocked = replace(snapshot, status="blocked", blocking_reason="TEST_SOURCE_DRIFT")
    raw_calls: list[object] = []
    state = gate.build_execution_state(
        source_snapshot=blocked,
        raw_reader=lambda *args, **kwargs: raw_calls.append(args) or pytest.fail("raw access"),
        module_loader=lambda: pytest.fail("module load"),
    )
    assert raw_calls == []
    assert state["counters"] == {
        "raw": 0, "decode": 0, "struct_parse": 0, "atom_parse": 0, "provider": 0,
    }
    assert state["sidecar_rows"] == []
    assert state["all_checks_passed"] is False


@pytest.mark.parametrize(
    "mutation",
    ["missing", "duplicate", "reorder", "identity", "path", "sha", "size"],
)
def test_exact11_join_rejects_drift(mutation: str) -> None:
    snapshot = gate.build_frozen_source_snapshot()
    passed, bindings, matrix, _ = gate._validate_p6b_predecessor(snapshot)
    assert passed
    bindings = copy.deepcopy(bindings)
    matrix = copy.deepcopy(matrix)
    if mutation == "missing":
        matrix.pop()
    elif mutation == "duplicate":
        matrix[1] = copy.deepcopy(matrix[0])
    elif mutation == "reorder":
        matrix[0], matrix[1] = matrix[1], matrix[0]
    elif mutation == "identity":
        matrix[0]["pdb_id"] = "DRIFT"
    elif mutation == "path":
        matrix[0]["raw_target_relative_path"] = "data/raw/covalent_sources/drift.cif"
    elif mutation == "sha":
        matrix[0]["observed_sha256"] = "0" * 64
    else:
        matrix[0]["observed_file_size_bytes"] = "1"
    assert gate._join_bindings_and_preconditions(bindings, matrix) == []


def test_secure_raw_read_returns_same_exact_bytes_and_closes_fds(tmp_path: Path) -> None:
    payload = b"same retained bytes\n"
    relative, _, digest = _raw_fixture(tmp_path, payload)
    result = gate.secure_read_expected_raw_source(
        relative, digest, len(payload), repo_root=tmp_path,
    )
    assert result.passed is True
    assert result.content_bytes is payload or result.content_bytes == payload
    assert result.observed_sha256 == hashlib.sha256(result.content_bytes).hexdigest() == digest
    assert result.observed_size_bytes == len(result.content_bytes) == len(payload)
    assert result.pre_stat_fingerprint == result.post_stat_fingerprint


@pytest.mark.parametrize("drift", ["path", "sha", "size"])
def test_secure_raw_read_rejects_invalid_path_sha_or_size(tmp_path: Path, drift: str) -> None:
    payload = b"expected raw bytes\n"
    relative, _, digest = _raw_fixture(tmp_path, payload)
    expected_path = "data/raw/covalent_sources/../escape.cif" if drift == "path" else relative
    expected_sha = "0" * 64 if drift == "sha" else digest
    expected_size = len(payload) + 1 if drift == "size" else len(payload)
    result = gate.secure_read_expected_raw_source(
        expected_path, expected_sha, expected_size, repo_root=tmp_path,
    )
    assert result.passed is False
    assert result.content_bytes == b""
    assert result.blocking_reason in {
        "RAW_SOURCE_INPUT_INVALID", "RAW_SOURCE_SHA256_MISMATCH",
        "RAW_SOURCE_SIZE_MISMATCH",
    }


@pytest.mark.parametrize("kind", ["parent_symlink", "final_symlink", "nonregular", "partial_read"])
def test_secure_raw_read_rejects_symlink_nonregular_and_partial(
    tmp_path: Path, kind: str,
) -> None:
    payload = b"fixture\n"
    relative = "data/raw/covalent_sources/synthetic/sample.cif"
    target = tmp_path / relative
    if kind == "parent_symlink":
        real = tmp_path / "real_raw"
        (real / "covalent_sources/synthetic").mkdir(parents=True)
        (real / "covalent_sources/synthetic/sample.cif").write_bytes(payload)
        (tmp_path / "data").mkdir()
        (tmp_path / "data/raw").symlink_to(real, target_is_directory=True)
    else:
        target.parent.mkdir(parents=True)
        if kind == "final_symlink":
            other = tmp_path / "other.cif"
            other.write_bytes(payload)
            target.symlink_to(other)
        elif kind == "nonregular":
            target.mkdir()
        else:
            target.write_bytes(payload)
    result = gate.secure_read_expected_raw_source(
        relative, hashlib.sha256(payload).hexdigest(), len(payload), repo_root=tmp_path,
        read_fn=(lambda fd, size: b"") if kind == "partial_read" else os.read,
    )
    assert result.passed is False
    if kind == "partial_read":
        assert result.blocking_reason == "RAW_SOURCE_PARTIAL_READ"
    elif kind == "nonregular":
        assert result.blocking_reason == "RAW_SOURCE_NOT_REGULAR_FILE"
    else:
        assert "SYMLINK" in result.blocking_reason or "SECURE_OPEN" in result.blocking_reason


def test_secure_raw_read_rejects_inode_or_stat_change(tmp_path: Path, monkeypatch) -> None:
    payload = b"stable until fstat\n"
    relative, _, digest = _raw_fixture(tmp_path, payload)
    original = os.fstat
    calls = 0

    def changed(fd: int):
        nonlocal calls
        calls += 1
        observed = original(fd)
        if calls < 2:
            return observed
        return SimpleNamespace(**{
            field: getattr(observed, field) + (1 if field == "st_ctime_ns" else 0)
            for field in gate.STAT_FIELDS
        })

    monkeypatch.setattr(gate.os, "fstat", changed)
    result = gate.secure_read_expected_raw_source(
        relative, digest, len(payload), repo_root=tmp_path,
    )
    assert result.passed is False
    assert result.blocking_reason == "RAW_SOURCE_CHANGED_DURING_READ"


def test_retained_bytes_survive_path_replacement_and_same_text_reaches_both_parsers(
    tmp_path: Path,
) -> None:
    payload = _synthetic_mmcif(struct_insertion="A", atom_insertion="A")
    relative, path, digest = _raw_fixture(tmp_path, payload)
    verified = gate.secure_read_expected_raw_source(
        relative, digest, len(payload), repo_root=tmp_path,
    )
    assert verified.passed
    path.unlink()
    path.write_bytes(b"replacement must not be parsed\n")
    p4, p5b = _modules()
    text_ids: list[int] = []
    texts: list[str] = []

    def parser(text: object, prefix: object):
        text_ids.append(id(text))
        texts.append(text)
        return p5b.parse_raw_preserving_mmcif_loop(text, prefix)

    binding = _binding(
        raw_target_relative_path=relative,
        expected_raw_sha256=digest,
        expected_raw_size_bytes=str(len(payload)),
    )
    row, evidence, counts = gate.execute_one_binding(
        binding, 1, p4=p4,
        p5b=SimpleNamespace(parse_raw_preserving_mmcif_loop=parser),
        repo_root=tmp_path, raw_reader=lambda *args, **kwargs: verified,
    )
    assert text_ids[0] == text_ids[1]
    assert texts == [payload.decode("utf-8")] * 2
    assert "replacement" not in texts[0]
    assert row["provider_export_status"] == "exported_pass"
    assert evidence["evidence_audit_passed"] is True
    assert counts == {"raw": 1, "decode": 1, "struct_parse": 1, "atom_parse": 1, "provider": 1}


def test_strict_utf8_decode_failure_skips_both_parsers_and_provider() -> None:
    parser_calls: list[object] = []
    provider_calls: list[object] = []
    p4, _ = _modules()
    p4_spy = SimpleNamespace(
        **{name: getattr(p4, name) for name in (
            "PARSER_INSERTION_SOURCE_TAGS", "resolve_locator_namespace_evidence",
            "validate_matched_atom_site_row_identity", "classify_insertion_code_raw_token",
            "resolve_insertion_code_evidence",
        )},
        build_locator_provider_export_fields=lambda **kwargs: provider_calls.append(kwargs),
    )
    row, evidence, counts = _execute(
        b"\xff\xfe", p4=p4_spy,
        p5b=SimpleNamespace(parse_raw_preserving_mmcif_loop=lambda *args: parser_calls.append(args)),
    )
    assert row["provider_export_status"] == "rejected"
    assert row["provider_export_blocking_reason"] == "RAW_MMCIF_UTF8_DECODE_FAILED"
    assert evidence["strict_decode_status"] == "failed"
    assert counts == {"raw": 1, "decode": 0, "struct_parse": 0, "atom_parse": 0, "provider": 0}
    assert parser_calls == provider_calls == []


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        (b"data_test\n", "MMCIF_LOOP_NOT_FOUND"),
        (b"data_test\nloop_\n_struct_conn.id\n'unterminated\n#\n", "MMCIF_TOKENIZATION_FAILED"),
        (b"data_test\nloop_\n_struct_conn.id\n_struct_conn.conn_type_id\nONLY_ONE\n#\n", "TOKEN_COUNT_NOT_DIVISIBLE:1:2"),
    ],
)
def test_parser_failures_reject_without_provider(payload: bytes, reason: str) -> None:
    row, _, counts = _execute(payload)
    assert row["provider_export_status"] == "rejected"
    assert row["provider_export_blocking_reason"] == reason
    assert counts["provider"] == 0


def _default_struct_row() -> list[str]:
    return [
        "CONN1", "covale", "CYS", "CYS", "SG", "SG", "A", "25", "A", "25", "?",
        "LIG", "LIG", "C2", "C2", "B", "1", "B", "1", ".",
    ]


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("missing", "STRUCT_CONN_EVENT_NOT_FOUND"),
        ("multiple", "MULTIPLE_STRUCT_CONN_EVENTS"),
        ("wrong_type", "STRUCT_CONN_TYPE_NOT_COVALE"),
        ("partner", "RESIDUE_PARTNER_SIDE_NOT_RESOLVED"),
        ("ligand", "LIGAND_PARTNER_IDENTITY_MISMATCH"),
        ("both_sides", "MULTIPLE_RESIDUE_PARTNER_SIDES"),
    ],
)
def test_real_event_selector_failures(mutation: str, reason: str) -> None:
    row = _default_struct_row()
    binding = _binding()
    rows = [row]
    if mutation == "missing":
        binding["conn_id"] = "MISSING"
    elif mutation == "multiple":
        rows.append(copy.deepcopy(row))
    elif mutation == "wrong_type":
        row[1] = "metalc"
    elif mutation == "partner":
        row[2] = row[3] = "ALA"
    elif mutation == "ligand":
        row[11] = row[12] = "BAD"
    else:
        binding["ligand_comp_id"] = "CYS"
        row[11] = row[12] = "CYS"
        row[13] = row[14] = "SG"
        row[15], row[16], row[17], row[18] = "A", "25", "A", "25"
    result, _, counts = _execute(
        _synthetic_mmcif(struct_rows=rows), binding=binding,
    )
    assert result["provider_export_status"] == "rejected"
    assert result["provider_export_blocking_reason"] == reason
    assert counts["provider"] == 0


@pytest.mark.parametrize(
    ("auth_pair", "label_pair", "expected_namespace", "expected_reason"),
    [
        (("A", "25"), ("X", "99"), "auth", ""),
        (("X", "99"), ("A", "25"), "label", ""),
        (("A", "25"), ("A", "25"), "auth", ""),
        (("X", "98"), ("Y", "99"), "", "LOCATOR_NAMESPACE_SELECTED_PAIR_NOT_FOUND"),
        (("A", "99"), ("X", "25"), "", "LOCATOR_NAMESPACE_MIXED_SELECTION_FORBIDDEN"),
    ],
)
def test_namespace_policy(
    auth_pair: tuple[str, str], label_pair: tuple[str, str],
    expected_namespace: str, expected_reason: str,
) -> None:
    event = gate.SelectedStructConnEvent(
        row=None, row_ordinal_1based=1, match_count=1,
        residue_partner_side="ptnr1",
        residue=tuple({
            "side": "ptnr1", "label_comp_id": "CYS", "auth_comp_id": "CYS",
            "label_atom_id": "SG", "auth_atom_id": "SG",
            "auth_asym_id": auth_pair[0], "auth_seq_id": auth_pair[1],
            "label_asym_id": label_pair[0], "label_seq_id": label_pair[1],
        }.items()),
        ligand=(),
    )
    assert gate.resolve_real_locator_namespace(event, _binding()) == (
        expected_namespace, expected_reason,
    )


def test_equal_dual_namespace_match_uses_auth_and_conflict_is_audited() -> None:
    row = _default_struct_row()
    row[7], row[8], row[9] = "25", "X", "99"
    result, _, _ = _execute(_synthetic_mmcif(struct_rows=[row]))
    assert result["locator_namespace"] == "auth"
    assert result["auth_label_conflict_observed"] is True


def test_label_namespace_and_ptnr2_success_paths() -> None:
    label_row = _default_struct_row()
    label_row[6], label_row[7], label_row[8], label_row[9] = "X", "99", "A", "25"
    label_row[10] = "."
    label_atom = ["101", "CYS", "CYS", "SG", "SG", "X", "99", "A", "25", "."]
    label_result, _, _ = _execute(_synthetic_mmcif(
        struct_rows=[label_row], atom_rows=[label_atom],
        struct_insertion=".", atom_insertion=".",
    ))
    assert label_result["locator_namespace"] == "label"
    assert label_result["provider_export_status"] == "exported_pass"

    ptnr2_row = [
        "CONN1", "covale", "LIG", "LIG", "C2", "C2", "B", "1", "B", "1", ".",
        "CYS", "CYS", "SG", "SG", "A", "25", "A", "25", "A",
    ]
    ptnr2_atom = ["101", "CYS", "CYS", "SG", "SG", "A", "25", "A", "25", "A"]
    ptnr2_result, _, _ = _execute(_synthetic_mmcif(
        struct_rows=[ptnr2_row], atom_rows=[ptnr2_atom],
    ))
    assert ptnr2_result["residue_partner_side"] == "ptnr2"
    assert ptnr2_result["struct_conn_insertion_source_tag"] == (
        "_struct_conn.pdbx_ptnr2_PDB_ins_code"
    )
    assert ptnr2_result["provider_export_status"] == "exported_pass"


@pytest.mark.parametrize(
    ("atom_rows", "reason"),
    [
        ([], "MATCHED_ATOM_SITE_ROW_NOT_FOUND"),
        ([
            ["101", "CYS", "CYS", "SG", "SG", "A", "25", "A", "25", "?"],
            ["102", "CYS", "CYS", "SG", "SG", "A", "25", "A", "25", "?"],
        ], "MULTIPLE_MATCHED_ATOM_SITE_ROWS"),
        ([["?", "CYS", "CYS", "SG", "SG", "A", "25", "A", "25", "?"]], "MATCHED_ATOM_SITE_ID_INVALID"),
        ([["101", "CYS", "CYS", "S", "S", "A", "25", "A", "25", "?"]], "MATCHED_ATOM_SITE_ROW_NOT_FOUND"),
    ],
)
def test_atom_site_unique_identity_failures(atom_rows: list[list[str]], reason: str) -> None:
    row, evidence, counts = _execute(_synthetic_mmcif(atom_rows=atom_rows))
    assert row["provider_export_status"] == "rejected"
    assert row["provider_export_blocking_reason"] == reason
    assert evidence["selected_atom_site_match_count"] in (0, 2, 1)
    assert counts["provider"] == 0


@pytest.mark.parametrize(
    ("struct_value", "atom_value", "struct_tag", "atom_tag", "status", "token_classes"),
    [
        ("A", "A", True, True, "exported_pass", ("explicit_token", "explicit_token")),
        (".", ".", True, True, "exported_pass", ("dot_not_applicable", "dot_not_applicable")),
        ("?", "?", True, True, "exported_blocking", ("question_unknown", "question_unknown")),
        ("", "", False, False, "exported_blocking", ("tag_missing", "tag_missing")),
        ("", "", True, True, "exported_blocking", ("parsed_empty", "parsed_empty")),
        ("A", "B", True, True, "exported_blocking", ("explicit_token", "explicit_token")),
        (" ", " ", True, True, "rejected", ("", "")),
    ],
)
def test_insertion_token_classes_and_provider_status(
    struct_value: str, atom_value: str, struct_tag: bool, atom_tag: bool,
    status: str, token_classes: tuple[str, str],
) -> None:
    row, _, counts = _execute(_synthetic_mmcif(
        struct_insertion=struct_value, atom_insertion=atom_value,
        include_struct_insertion=struct_tag, include_atom_insertion=atom_tag,
    ))
    assert row["provider_export_status"] == status
    if status == "rejected":
        assert "INSERTION_RAW_VALUE_WHITESPACE_INVALID" in row["provider_export_blocking_reason"]
        assert counts["provider"] == 0
    else:
        assert (row["struct_conn_token_class"], row["atom_site_token_class"]) == token_classes
        assert counts["provider"] == 1


@pytest.mark.parametrize("exception", [TypeError("TYPE_PROVIDER_FAILURE"), ValueError("VALUE_PROVIDER_FAILURE")])
def test_provider_type_and_value_errors_become_rejected_without_partial_fields(exception: Exception) -> None:
    p4, _ = _modules()
    names = (
        "PARSER_INSERTION_SOURCE_TAGS", "resolve_locator_namespace_evidence",
        "validate_matched_atom_site_row_identity", "classify_insertion_code_raw_token",
        "resolve_insertion_code_evidence",
    )

    def fail(**kwargs):
        raise exception

    fake = SimpleNamespace(
        **{name: getattr(p4, name) for name in names},
        build_locator_provider_export_fields=fail,
    )
    row, _, counts = _execute(
        _synthetic_mmcif(struct_insertion="A", atom_insertion="A"), p4=fake,
    )
    assert row["provider_export_status"] == "rejected"
    assert row["provider_export_blocking_reason"] == str(exception)
    assert all(row[field] == "" for field in (
        "covalent_residue_locator_namespace",
        "covalent_residue_insertion_code_state",
        "covalent_residue_insertion_code",
        "covalent_residue_locator_provenance_source_id",
        "covalent_residue_locator_provenance_sha256",
    ))
    assert counts["provider"] == 1


def test_real_exact11_identity_order_provenance_and_evidence(real_state) -> None:
    p4, _ = _modules()
    rows = real_state["sidecar_rows"]
    evidence = real_state["evidence_rows"]
    assert real_state["extracted_schemas"]["p6a_future_real_sidecar_columns"] == gate.FUTURE_REAL_SIDECAR_COLUMNS
    assert gate.validate_sidecar_rows(rows, real_state["joined_rows"], p4=p4)
    assert gate.validate_evidence_rows(evidence, rows, real_state["joined_rows"])
    assert [row["binding_row_id"] for row in rows] == [
        f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)
    ]
    assert [row["smoke_case_id"] for row in rows] == [
        f"P6C_REAL_{index:06d}" for index in range(1, 12)
    ]
    assert all(tuple(row) == gate.FUTURE_REAL_SIDECAR_COLUMNS for row in rows)
    assert real_state["counters"] == {
        "raw": 11, "decode": 11, "struct_parse": 11, "atom_parse": 11, "provider": 11,
    }
    assert real_state["provider_row_count"] == 11
    assert real_state["rejected_count"] == 0
    assert len(set(real_state["source_ids"])) == 11
    assert len(set(real_state["provenance_hashes"])) == 11


@pytest.mark.parametrize("drift", ["order", "identity", "status", "source_id", "sha"])
def test_sidecar_validator_rejects_drift(real_state, drift: str) -> None:
    p4, _ = _modules()
    rows = copy.deepcopy(real_state["sidecar_rows"])
    if drift == "order":
        rows[0], rows[1] = rows[1], rows[0]
    elif drift == "identity":
        rows[0]["pdb_id"] = "DRIFT"
    elif drift == "status":
        rows[0]["provider_export_status"] = "invalid"
    elif drift == "source_id":
        rows[0]["covalent_residue_locator_provenance_source_id"] += "-drift"
    else:
        rows[0]["covalent_residue_locator_provenance_sha256"] = "0" * 64
    assert not gate.validate_sidecar_rows(rows, real_state["joined_rows"], p4=p4)


def test_evidence_and_contract_full_row_validators_reject_drift(real_state) -> None:
    evidence = copy.deepcopy(real_state["evidence_rows"])
    evidence[0]["selected_atom_site_row_ordinal_1based"] = 0
    assert not gate.validate_evidence_rows(
        evidence, real_state["sidecar_rows"], real_state["joined_rows"],
    )
    contract = copy.deepcopy(real_state["contract_rows"])
    contract[0]["observed_value"] = "10"
    assert not gate.validate_contract_rows(contract, real_state["observations"])
    assert [row["issue_id"] for row in real_state["issue_rows"]] == [
        "REAL_PROVIDER_SIDECAR_NOT_YET_MERGED_INTO_ADMISSION_SCHEMA",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
    ]
    assert all(row["safety_passed"] is True for row in real_state["safety_rows"])


def test_exact_outputs_double_materialization_atomic_replace_and_checker_fail_closed(
    tmp_path: Path,
) -> None:
    checker = _load_checker()
    root = tmp_path / "outputs"
    first = gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1(root)
    checker._validate_result(first, root)
    first_bytes = {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    assert {
        name: hashlib.sha256(content).hexdigest()
        for name, content in first_bytes.items()
    } == EXPECTED_OUTPUT_SHA256
    second = gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1(root)
    checker._validate_result(second, root)
    assert first_bytes == {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    assert not list(root.glob("*.tmp")) and not list(root.glob("*.part"))

    missing = root / gate.CONTRACT_FILENAME
    missing_bytes = missing.read_bytes()
    missing.unlink()
    with pytest.raises(AssertionError):
        checker._validate_result(second, root)
    missing.write_bytes(missing_bytes)

    extra = root / "extra.csv"
    extra.write_text("extra\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker._validate_result(second, root)
    extra.unlink()

    safety = root / gate.SAFETY_FILENAME
    safety_bytes = safety.read_bytes()
    safety.unlink()
    safety.symlink_to(root / gate.CONTRACT_FILENAME)
    with pytest.raises(AssertionError):
        checker._validate_result(second, root)
    safety.unlink()
    safety.write_bytes(safety_bytes)

    sidecar = root / gate.SIDECAR_FILENAME
    sidecar_bytes = sidecar.read_bytes()
    sidecar.write_bytes(sidecar_bytes + b"drift\n")
    with pytest.raises(AssertionError):
        checker._validate_result(second, root)
    sidecar.write_bytes(sidecar_bytes)

    manifest_path = root / gate.MANIFEST_FILENAME
    manifest_bytes = manifest_path.read_bytes()
    payload = json.loads(manifest_bytes)
    payload["ready_for_training"] = True
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(AssertionError):
        checker._validate_result(second, root)
    manifest_path.write_bytes(manifest_bytes)
    checker._validate_result(second, root)


def test_import_has_no_output_side_effect(tmp_path: Path) -> None:
    code = (
        "import pathlib; "
        "import covalent_ext.covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke; "
        "print(sorted(p.name for p in pathlib.Path('.').iterdir()))"
    )
    result = subprocess.run(
        [sys.executable, "-B", "-c", code], cwd=tmp_path,
        env={"PYTHONPATH": str(REPO_ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
        check=True, text=True, capture_output=True,
    )
    assert result.stdout.strip() == "[]"
