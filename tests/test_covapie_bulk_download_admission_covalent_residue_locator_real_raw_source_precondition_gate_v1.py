from __future__ import annotations

import errno
import copy
import csv
import hashlib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
from covalent_ext import (
    covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate
    as gate,
)
CHECK_PATH = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("p6b_checker", CHECK_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sources():
    snapshot = gate._build_frozen_source_snapshot()
    assert gate.validate_frozen_source_snapshot(snapshot, REPO_ROOT)
    return snapshot


def _materialize_source_fixture(root: Path) -> gate.FrozenSourceSnapshot:
    snapshot = _sources()
    for record in snapshot.records:
        path = root / record.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(record.content_bytes)
    return snapshot


def _documents():
    sources = _sources()
    return (
        gate._read_frozen_csv(gate.P6A_BINDING_PATH, sources),
        gate._read_frozen_csv(gate.P6B0_AUTHORITY_PATH, sources),
        gate._read_frozen_csv(gate.EXPANSION_AUTHORITY_PATH, sources),
    )


def _raw_fixture(root: Path, name: str = "sample.cif", payload: bytes = b"raw bytes\n") -> tuple[str, Path]:
    relative = f"data/raw/covalent_sources/synthetic/{name}"
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return relative, path


def _result(returncode: int) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], returncode, "", "")


def _git_provider(*, tracked: bool, ignored: bool, worktree_clean: bool = True, index_clean: bool = True):
    def provider(args, _root):
        command = tuple(args[:2])
        if command == ("ls-files", "--error-unmatch"):
            return _result(0 if tracked else 1)
        if command == ("diff", "--quiet"):
            return _result(0 if worktree_clean else 1)
        if command == ("diff", "--cached"):
            return _result(0 if index_clean else 1)
        if command == ("check-ignore", "-q"):
            return _result(0 if ignored else 1)
        raise AssertionError(args)
    return provider


def test_fixed_names_sources_and_headers():
    assert gate.STEP_LABEL == "Step14AU-E0-P6-B"
    assert len(gate.SOURCE_PATHS) == len(gate.SOURCE_SHA256) == 9
    assert tuple(gate.SOURCE_SHA256) == tuple(map(str, gate.SOURCE_PATHS))
    assert len(gate.MATRIX_COLUMNS) == 31
    assert len(gate.CONTRACT_SPECS) == 50
    assert len(gate.OUTPUT_FILES) == 6
    assert len(gate.CANONICAL_MASK_PAIRS) == 5
    assert ("scaffold_only", "B3") in gate.CANONICAL_MASK_PAIRS


def test_source_boundary_exact_order_hash_tracking_regular_non_symlink():
    rows = list(_sources().source_rows)
    assert rows == gate._canonical_source_rows()
    assert [row["source_order"] for row in rows] == list(range(1, 10))


@pytest.mark.parametrize("field,value", [
    ("tracked", False), ("regular_file", False), ("symlink", True),
    ("sha256_observed", "0" * 64),
])
def test_source_boundary_rejects_drift(field, value):
    rows = gate._canonical_source_rows()
    rows[0][field] = value
    assert not gate.validate_source_rows(rows)


def test_source_structural_failure_happens_before_content_open(tmp_path, monkeypatch):
    calls = []
    original = Path.open
    monkeypatch.setattr(Path, "open", lambda self, *a, **k: calls.append(self) or original(self, *a, **k))
    rows = gate._source_rows(tmp_path)
    assert not gate.validate_source_rows(rows)
    assert calls == []


def test_frozen_reader_rejects_unvalidated_snapshot(monkeypatch):
    blocked = gate.FrozenSourceSnapshot(
        gate.RepoRootIdentity("", (0, 0, 0)), (), (), "blocked", "TEST", 0
    )
    monkeypatch.setattr(gate, "_parse_csv_bytes", lambda _bytes: pytest.fail("content parse"))
    assert gate._read_frozen_csv(gate.P6A_BINDING_PATH, blocked).blocking_reason == "SOURCE_ACCESS_NOT_ALLOWED"


def test_p6b0_and_p6a_predecessors_are_frozen():
    bindings, historical, expansion = _documents()
    manifest = gate._read_frozen_json(gate.P6B0_MANIFEST_PATH, _sources())
    assert manifest.status == "passed"
    assert all(gate._p6b0_checks(manifest.payload, historical).values())
    assert all(gate._p6a_checks(bindings).values())
    assert all(gate._expansion_checks(expansion).values())


def test_authority_mapping_exact_11_order_and_scopes():
    bindings, historical, expansion = _documents()
    rows = gate._authority_mapping(bindings, historical, expansion)
    assert gate.validate_authority_mapping(rows)
    assert len(rows) == 11
    assert [row["authority_scope"] for row in rows] == ["historical_committed_consensus"] * 3 + ["expansion_committed_fingerprint"] * 8
    assert [row["authority_row_id"] for row in rows] == [
        "HISTORICAL_RAW_AUTHORITY_000001", "HISTORICAL_RAW_AUTHORITY_000002",
        "HISTORICAL_RAW_AUTHORITY_000003", *[f"FP_{i:06d}" for i in range(1, 9)],
    ]
    assert [(row["pdb_id"], row["ligand"]) for row in rows] == list(gate.HISTORICAL_IDENTITIES + gate.EXPANSION_IDENTITIES)


@pytest.mark.parametrize("document_index,row_index,field,value", [
    (0, 0, "pdb_id", "MISSING"),
    (0, 1, "pdb_id", "6BV6"),
    (0, 0, "raw_target_relative_path", "data/raw/covalent_sources/wrong.cif"),
    (1, 0, "expected_sha256", "0" * 64),
    (1, 0, "expected_file_size_bytes", "0"),
    (1, 0, "authority_status", "failed"),
    (2, 0, "expected_sha256", "f" * 64),
])
def test_authority_mapping_rejects_missing_duplicate_conflict_or_drift(document_index, row_index, field, value):
    documents = list(_documents())
    document = documents[document_index]
    rows = [dict(row) for row in document.rows]
    rows[row_index][field] = value
    documents[document_index] = gate.CsvDocument(document.header, tuple(rows), document.status, document.blocking_reason)
    assert gate._authority_mapping(*documents) == []


def test_authority_failure_prevents_all_raw_access():
    sources = gate._canonical_source_rows()
    sources[0]["sha256_observed"] = "0" * 64
    calls = []
    state = gate.build_precondition_state(
        source_rows=sources,
        raw_reader=lambda *a, **k: calls.append(a) or pytest.fail("raw access"),
    )
    assert calls == []
    assert state["raw_open_count"] == state["raw_stat_count"] == state["raw_read_count"] == state["raw_hash_count"] == 0
    assert state["sections"]["source_boundary"] is False
    assert state["sections"]["authority_mapping"] is False


def test_linux_platform_fd_contract():
    assert all(gate._platform_checks().values())
    source = inspect.getsource(gate.secure_hash_raw_source)
    assert "O_NOFOLLOW" in source and "O_DIRECTORY" in source and "O_CLOEXEC" in source
    for forbidden in ("Path.open", "Path.resolve", "read_bytes", "read_text", "builtins.open", ".decode("):
        assert forbidden not in source


def test_secure_raw_access_valid_regular_file(tmp_path):
    relative, path = _raw_fixture(tmp_path, payload=b"a" * (gate.CHUNK_SIZE + 13))
    result = gate.secure_hash_raw_source(relative, repo_root=tmp_path)
    assert result.exists and result.regular and not result.symlink and result.confined
    assert result.stat_stable and result.bytes_read == path.stat().st_size
    assert result.pre_fingerprint == result.post_fingerprint
    assert result.directory_component_open_count == len(Path(relative).parts)
    assert result.final_entry_stat_performed and result.file_fd_opened
    assert result.fd_fstat_performed and result.read_completed and result.hash_completed
    assert result.blocking_reason == ""


@pytest.mark.parametrize("value", [
    "/data/raw/covalent_sources/x.cif", "data/raw/covalent_sources/../x.cif",
    "file:data/raw/covalent_sources/x.cif", "C:/data/raw/covalent_sources/x.cif",
    "data\\raw\\covalent_sources\\x.cif", "data/raw/covalent_sources/./x.cif",
    "data/raw/covalent_sources/?/x.cif", "data/raw/covalent_sources/x.CIF",
    "data/raw/wrong/x.cif", " data/raw/covalent_sources/x.cif ",
])
def test_secure_raw_access_rejects_escape_absolute_uri_drive_dotdot(value, tmp_path):
    result = gate.secure_hash_raw_source(value, repo_root=tmp_path)
    assert result.blocking_reason == "RAW_TARGET_PATH_INVALID"


def test_raw_path_rejects_string_subclass():
    class StringSubclass(str):
        pass
    assert gate._safe_raw_relative_path(StringSubclass(gate.HISTORICAL_RAW_PATHS[0])) is False


def test_secure_raw_access_rejects_parent_symlink(tmp_path):
    target = tmp_path / "outside"
    target.mkdir()
    (target / "sample.cif").write_bytes(b"x")
    parent = tmp_path / "data/raw/covalent_sources"
    parent.mkdir(parents=True)
    (parent / "synthetic").symlink_to(target, target_is_directory=True)
    result = gate.secure_hash_raw_source("data/raw/covalent_sources/synthetic/sample.cif", repo_root=tmp_path)
    assert not result.stat_stable and result.observed_sha256 == ""
    assert not result.final_entry_stat_performed
    assert not result.file_fd_opened and not result.hash_completed


def test_secure_raw_access_rejects_final_symlink(tmp_path):
    relative, path = _raw_fixture(tmp_path, "target.cif")
    link = path.with_name("link.cif")
    link.symlink_to(path)
    result = gate.secure_hash_raw_source(
        relative.replace("target.cif", "link.cif"), repo_root=tmp_path,
        read_fn=lambda _fd, _size: pytest.fail("symlink target read"),
    )
    assert result.exists and not result.regular and result.symlink and not result.confined
    assert not result.stat_stable and result.observed_sha256 == ""
    assert result.final_entry_stat_performed
    assert not result.file_fd_opened and not result.fd_fstat_performed
    assert not result.read_completed and not result.hash_completed
    assert result.blocking_reason == "RAW_FINAL_ENTRY_SYMLINK_REJECTED"


def test_secure_raw_access_missing_and_directory(tmp_path):
    missing = gate.secure_hash_raw_source("data/raw/covalent_sources/synthetic/missing.cif", repo_root=tmp_path)
    assert missing.blocking_reason in {"RAW_SOURCE_MISSING", "RAW_PARENT_NOT_DIRECTORY"}
    relative, path = _raw_fixture(tmp_path)
    path.unlink()
    path.mkdir()
    directory = gate.secure_hash_raw_source(relative, repo_root=tmp_path)
    assert directory.exists and not directory.regular and not directory.symlink
    assert directory.final_entry_stat_performed and not directory.file_fd_opened
    assert directory.blocking_reason == "RAW_SOURCE_NOT_REGULAR_FILE"


def test_secure_raw_access_detects_partial_read(tmp_path):
    relative, _ = _raw_fixture(tmp_path, payload=b"abcdef")
    called = False
    def partial(fd, size):
        nonlocal called
        if called:
            return b""
        called = True
        return os.read(fd, 2)
    result = gate.secure_hash_raw_source(relative, repo_root=tmp_path, read_fn=partial)
    assert result.blocking_reason == "RAW_SOURCE_PARTIAL_READ"
    assert not result.stat_stable and result.observed_sha256 == ""
    assert result.file_fd_opened and result.fd_fstat_performed
    assert not result.read_completed and not result.hash_completed


def test_secure_raw_access_detects_pre_entry_open_inode_replacement(tmp_path):
    relative, path = _raw_fixture(tmp_path, payload=b"original")
    def replace_after_entry_stat():
        replacement = path.with_suffix(".replacement")
        replacement.write_bytes(b"replacement")
        os.replace(replacement, path)
    result = gate.secure_hash_raw_source(
        relative, repo_root=tmp_path,
        after_entry_stat_hook=replace_after_entry_stat,
    )
    assert result.blocking_reason == "RAW_SOURCE_CHANGED_DURING_OPEN"
    assert result.exists and result.regular and result.confined
    assert result.final_entry_stat_performed and result.file_fd_opened
    assert result.fd_fstat_performed and not result.hash_completed
    assert result.observed_sha256 == "" and not result.stat_stable


@pytest.mark.parametrize("mutation", ["replace", "truncate", "mtime"])
def test_secure_raw_access_detects_replacement_size_or_time_change(tmp_path, mutation):
    relative, path = _raw_fixture(tmp_path, payload=b"abcdef")
    def hook(_fd):
        if mutation == "replace":
            replacement = path.with_suffix(".new")
            replacement.write_bytes(b"abcdef")
            os.replace(replacement, path)
        elif mutation == "truncate":
            path.write_bytes(b"a")
        else:
            os.utime(path, ns=(path.stat().st_atime_ns, path.stat().st_mtime_ns + 1_000_000))
    result = gate.secure_hash_raw_source(relative, repo_root=tmp_path, after_read_hook=hook)
    assert result.blocking_reason == "RAW_SOURCE_CHANGED_DURING_HASH"
    assert not result.stat_stable and result.observed_sha256 == ""


def test_secure_raw_access_closes_every_fd(tmp_path, monkeypatch):
    relative, _ = _raw_fixture(tmp_path)
    closed = []
    original = os.close
    monkeypatch.setattr(gate.os, "close", lambda fd: closed.append(fd) or original(fd))
    result = gate.secure_hash_raw_source(relative, repo_root=tmp_path)
    assert result.stat_stable and len(closed) == 6
    assert len(set(closed)) == len(closed)


def test_git_untracked_historical_authority_runtime_passes_without_ignore_dependency(tmp_path):
    state = gate._git_state(gate.HISTORICAL_RAW_PATHS[0], "historical_committed_consensus", repo_root=tmp_path, git_provider=_git_provider(tracked=False, ignored=False))
    assert state == {"state": "untracked_historical_authority_runtime", "tracked": False, "ignored": False, "worktree_clean": True, "index_clean": True, "passed": True}


@pytest.mark.parametrize("tracked,index,path", [
    (True, True, gate.HISTORICAL_RAW_PATHS[0]),
    (False, False, gate.HISTORICAL_RAW_PATHS[0]),
    (False, True, "data/raw/covalent_sources/noncanonical.cif"),
])
def test_git_historical_tracked_staged_or_noncanonical_fails(tmp_path, tracked, index, path):
    state = gate._git_state(path, "historical_committed_consensus", repo_root=tmp_path, git_provider=_git_provider(tracked=tracked, ignored=True, index_clean=index))
    assert not state["passed"] and state["state"] == "unknown"


def test_git_ignored_expansion_passes(tmp_path):
    state = gate._git_state(gate.EXPANSION_RAW_PATHS[0], "expansion_committed_fingerprint", repo_root=tmp_path, git_provider=_git_provider(tracked=False, ignored=True))
    assert state == {"state": "ignored_runtime", "tracked": False, "ignored": True, "worktree_clean": True, "index_clean": True, "passed": True}


@pytest.mark.parametrize("tracked,ignored,index", [
    (True, True, True), (False, False, True), (False, True, False),
])
def test_git_expansion_tracked_nonignored_or_staged_fails(tmp_path, tracked, ignored, index):
    state = gate._git_state(gate.EXPANSION_RAW_PATHS[0], "expansion_committed_fingerprint", repo_root=tmp_path, git_provider=_git_provider(tracked=tracked, ignored=ignored, index_clean=index))
    assert not state["passed"] and state["state"] == "unknown"


def test_unknown_git_scope_fails(tmp_path):
    state = gate._git_state("x", "unknown", repo_root=tmp_path, git_provider=_git_provider(tracked=False, ignored=True))
    assert not state["passed"]


def test_real_canonical_revalidation_succeeds_with_corrected_git_policy():
    state = gate.build_precondition_state()
    assert len(state["mapping"]) == len(state["matrix_rows"]) == 11
    assert state["passed_count"] == 11 and state["blocked_count"] == 0
    assert [row["pdb_id"] for row in state["matrix_rows"][:3]] == ["6BV6", "6BV8", "6BV5"]
    assert all(row["raw_git_tracking_state"] == "untracked_historical_authority_runtime" for row in state["matrix_rows"][:3])
    assert all(row["raw_git_tracking_state"] == "ignored_runtime" for row in state["matrix_rows"][3:])
    assert all(row["blocking_reason"] == "" for row in state["matrix_rows"])
    assert all(row["sha256_matches"] and row["file_size_matches"] and row["stat_stable"] for row in state["matrix_rows"])
    assert state["sections"]["raw_access"] is True
    assert state["all_checks_passed"] is True


def test_matrix_authority_contract_safety_and_issues_shapes():
    state = gate.build_precondition_state()
    assert len(state["matrix_rows"]) == 11
    assert all(tuple(row) == gate.MATRIX_COLUMNS for row in state["matrix_rows"])
    assert len(state["authority_audit_rows"]) == 2
    assert all(tuple(row) == gate.AUTHORITY_AUDIT_COLUMNS for row in state["authority_audit_rows"])
    assert len(state["contract_rows"]) == 50
    assert all(tuple(row) == gate.CONTRACT_COLUMNS for row in state["contract_rows"])
    assert gate.validate_issue_rows(state["issue_rows"])
    assert gate.validate_authority_mapping(state["mapping"])
    assert gate.validate_authority_audit_rows(state["authority_audit_rows"], state["mapping"])
    assert gate.validate_matrix_rows(
        state["matrix_rows"], state["mapping"],
        state["raw_observations"], state["git_states"],
    )
    assert gate.validate_contract_rows(state["contract_rows"], state["observations"])
    assert gate.validate_safety_rows(state["safety_rows"], state["execution"])
    assert tuple(state["sections"]) == gate.SECTION_NAMES


def test_contract_is_evidence_driven_and_canonical_observations_can_pass():
    observations = {requirement: expected for _, _, requirement, expected in gate.CONTRACT_SPECS}
    rows = gate._contract_rows(observations)
    assert gate.validate_contract_rows(rows, observations)
    observations["sha256_match_count"] = 10
    rows = gate._contract_rows(observations)
    assert not gate.validate_contract_rows(rows, observations)
    assert next(row for row in rows if row["requirement"] == "sha256_match_count")["contract_passed"] is False


def test_issue_inventory_full_equality_and_removed_old_issues():
    rows = gate._issue_rows()
    assert gate.validate_issue_rows(rows)
    assert [row["issue_count"] for row in rows] == [11, 1]
    assert all("REAL_RAW_SOURCE_PRECONDITION_NOT_YET_EXECUTED" not in row["issue_id"] for row in rows)
    assert all("REAL_RAW_SOURCE_SHA256_PRECONDITION_NOT_YET_FROZEN" not in row["issue_id"] for row in rows)


def test_double_materialization_is_byte_identical(tmp_path):
    root = tmp_path / "outputs"
    first = gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1(root)
    first_bytes = {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    second = gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1(root)
    assert {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES} == first_bytes
    assert first["manifest"] == second["manifest"]
    assert {path.name for path in root.iterdir()} == set(gate.OUTPUT_FILES)
    assert not tuple(root.glob("*.tmp"))


def test_output_root_symlink_and_non_directory_fail(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(RuntimeError, match="OUTPUT_ROOT_NOT_SAFE_DIRECTORY"):
        gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1(link)
    file_root = tmp_path / "file"
    file_root.write_text("x")
    with pytest.raises(RuntimeError, match="OUTPUT_ROOT_NOT_SAFE_DIRECTORY"):
        gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1(file_root)


def test_manifest_canonical_readiness_and_truth():
    state = gate.build_precondition_state()
    manifest = gate._manifest_payload(state, {name: "0" * 64 for name in gate.CSV_OUTPUTS})
    assert manifest["all_checks_passed"] is True
    assert manifest["ready_for_real_provider_export_execution_smoke"] is True
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    assert manifest["untracked_historical_authority_runtime_count"] == 3
    assert manifest["ignored_expansion_runtime_count"] == 8
    assert manifest["exact_raw_tracked_count"] == 0
    assert manifest["real_raw_sources_stat_current_step"] is True
    assert manifest["real_raw_sources_read_current_step"] is True
    assert manifest["real_raw_sources_hashed_current_step"] is True
    assert manifest["real_raw_sources_parsed_current_step"] is False
    assert manifest["p5b_parser_called_current_step"] is False
    assert manifest["p4_provider_called_current_step"] is False
    assert manifest["real_provider_rows_materialized_current_step"] is False
    assert manifest["real_samples_backfilled_current_step"] == 0
    assert manifest["existing_real_sample_count"] == 11
    assert manifest["real_insertion_unknown_sample_count"] == 11
    assert manifest["real_insertion_absence_proven_sample_count"] == 0
    assert manifest["feature_semantics_audit_required_before_training"] is True


@pytest.mark.parametrize("mutation", [
    "empty", "reorder", "scope", "source", "authority_id", "pipeline",
    "sample", "raw_path", "coordinated_identity", "extra_key",
])
def test_authority_mapping_full_row_validator_rejects_all_drift(mutation):
    rows = copy.deepcopy(gate._canonical_authority_mapping())
    if mutation == "empty":
        rows = []
    elif mutation == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "scope":
        rows[0]["authority_scope"] = "expansion_committed_fingerprint"
    elif mutation == "source":
        rows[0]["authority_source"] = str(gate.EXPANSION_AUTHORITY_PATH)
    elif mutation == "authority_id":
        rows[0]["authority_row_id"] = "FP_000001"
    elif mutation == "pipeline":
        rows[0]["source_pipeline"] = "drift"
    elif mutation == "sample":
        rows[0]["sample_id"] = rows[1]["sample_id"]
    elif mutation == "raw_path":
        rows[0]["raw_path"] = rows[1]["raw_path"]
    elif mutation == "coordinated_identity":
        rows[0]["pdb_id"] = "9XYZ"
        rows[0]["ligand"] = "XYZ"
    else:
        rows[0]["extra"] = "drift"
    assert not gate.validate_authority_mapping(rows)


def test_authority_audit_actual_counts_and_partial_mapping_truth():
    mapping = gate._canonical_authority_mapping()
    rows = gate._authority_audit_rows(mapping, True)
    assert gate.validate_authority_audit_rows(rows, mapping)
    assert [row["authority_row_count"] for row in rows] == [3, 8]
    partial = mapping[:-1]
    partial_rows = gate._authority_audit_rows(partial, False)
    assert [row["authority_row_count"] for row in partial_rows] == [3, 7]
    assert [row["binding_match_count"] for row in partial_rows] == [3, 7]
    assert not gate.validate_authority_audit_rows(partial_rows, partial)


@pytest.mark.parametrize("mutation", ["reorder", "count", "passed", "reason", "coordinated"])
def test_authority_audit_full_row_validator_rejects_drift(mutation):
    mapping = gate._canonical_authority_mapping()
    rows = copy.deepcopy(gate._authority_audit_rows(mapping, True))
    if mutation == "reorder":
        rows.reverse()
    elif mutation == "count":
        rows[0]["authority_row_count"] = 2
    elif mutation == "passed":
        rows[0]["authority_check_passed"] = False
    elif mutation == "reason":
        rows[0]["blocking_reason"] = "DRIFT"
    else:
        rows[0]["authority_row_count"] = 2
        rows[0]["binding_match_count"] = 2
        rows[0]["expected_hash_count"] = 2
        rows[0]["prior_observed_match_count"] = 2
        rows[0]["expected_size_count"] = 2
    assert not gate.validate_authority_audit_rows(rows, mapping)


@pytest.mark.parametrize("mutation", [
    "empty", "reorder", "identity", "authority", "git", "sha", "size",
    "stat", "status", "ready", "reason", "extra",
])
def test_matrix_full_row_validator_rejects_drift_and_overclaim(mutation):
    state = gate.build_precondition_state()
    rows = copy.deepcopy(state["matrix_rows"])
    if mutation == "empty":
        rows = []
    elif mutation == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "identity":
        rows[0]["pdb_id"] = "9XYZ"
        rows[0]["ligand_comp_id"] = "XYZ"
    elif mutation == "authority":
        rows[0]["expected_authority_row_id"] = "FP_000001"
    elif mutation == "git":
        rows[0]["raw_git_tracking_state"] = "ignored_runtime"
    elif mutation == "sha":
        rows[0]["expected_sha256"] = rows[0]["observed_sha256"] = "0" * 64
    elif mutation == "size":
        rows[0]["expected_file_size_bytes"] = rows[0]["observed_file_size_bytes"] = 1
    elif mutation == "stat":
        rows[0]["pre_hash_stat_fingerprint"] = rows[0]["post_hash_stat_fingerprint"] = "dev=1"
    elif mutation == "status":
        rows[0]["raw_source_precondition_status"] = "blocked"
    elif mutation == "ready":
        rows[0]["ready_for_real_provider_export_execution_smoke"] = False
    elif mutation == "reason":
        rows[0]["blocking_reason"] = "DRIFT"
    else:
        rows[0]["extra"] = "drift"
    assert not gate.validate_matrix_rows(
        rows, state["mapping"], state["raw_observations"], state["git_states"]
    )


def _fingerprint_with(value, **changes):
    names = ("dev", "ino", "mode", "nlink", "size", "mtime_ns", "ctime_ns")
    parsed = gate._parse_stat_fingerprint(value)
    assert parsed is not None
    fields = dict(zip(names, parsed))
    fields.update(changes)
    return ";".join(f"{name}={fields[name]}" for name in names)


@pytest.mark.parametrize("mutation", [
    "wrong_size", "nonregular_mode", "zero_nlink", "coordinated_valid_drift",
])
def test_stat_fingerprint_semantics_reject_coordinated_evidence_drift(mutation):
    state = gate.build_precondition_state()
    observations = list(state["raw_observations"])
    original = observations[0]
    if mutation == "wrong_size":
        fingerprint = _fingerprint_with(original.pre_fingerprint, size=original.observed_size + 1)
    elif mutation == "nonregular_mode":
        fingerprint = _fingerprint_with(original.pre_fingerprint, mode=1)
    elif mutation == "zero_nlink":
        fingerprint = _fingerprint_with(original.pre_fingerprint, nlink=0)
    else:
        fingerprint = "dev=1;ino=1;mode=1;nlink=1;size=1;mtime_ns=1;ctime_ns=1"
    observations[0] = replace(original, pre_fingerprint=fingerprint, post_fingerprint=fingerprint)
    rows = gate._build_matrix_rows(state["mapping"], observations, state["git_states"])
    assert rows[0]["pre_hash_stat_fingerprint"] == rows[0]["post_hash_stat_fingerprint"]
    assert not gate.validate_matrix_rows(rows, state["mapping"], observations, state["git_states"])


def test_matrix_validator_binds_rows_to_original_observation_evidence():
    state = gate.build_precondition_state()
    rows = copy.deepcopy(state["matrix_rows"])
    rows[0]["pre_hash_stat_fingerprint"] = rows[0]["post_hash_stat_fingerprint"] = _fingerprint_with(
        rows[0]["pre_hash_stat_fingerprint"], mtime_ns=1
    )
    assert not gate.validate_matrix_rows(
        rows, state["mapping"], state["raw_observations"], state["git_states"]
    )


def test_stat_fingerprint_size_must_match_observed_and_authority_sizes():
    state = gate.build_precondition_state()
    observations = list(state["raw_observations"])
    original = observations[0]
    fingerprint = _fingerprint_with(original.pre_fingerprint, size=original.observed_size + 1)
    observations[0] = replace(original, pre_fingerprint=fingerprint, post_fingerprint=fingerprint)
    rows = gate._build_matrix_rows(state["mapping"], observations, state["git_states"])
    assert gate._parse_stat_fingerprint(fingerprint)[4] != rows[0]["observed_file_size_bytes"]
    assert gate._parse_stat_fingerprint(fingerprint)[4] != rows[0]["expected_file_size_bytes"]
    assert not gate.validate_matrix_rows(rows, state["mapping"], observations, state["git_states"])


@pytest.mark.parametrize("mutation", ["missing", "reorder", "coordinated", "manual_pass", "reason"])
def test_contract_full_row_validator_rejects_coordinated_drift(mutation):
    state = gate.build_precondition_state()
    rows = copy.deepcopy(state["contract_rows"])
    if mutation == "missing":
        rows.pop()
    elif mutation == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "coordinated":
        rows[0]["expected_value"] = rows[0]["observed_value"] = "drift"
    elif mutation == "manual_pass":
        rows[0]["observed_value"] = "drift"
        rows[0]["contract_passed"] = True
    else:
        rows[0]["blocking_reason"] = "DRIFT"
    assert not gate.validate_contract_rows(rows, state["observations"])


class _FailingObservations(dict):
    def get(self, key, default=None):
        raise ValueError("observation failure")


def test_contract_validator_rejects_observation_helper_failure():
    state = gate.build_precondition_state()
    assert not gate.validate_contract_rows(state["contract_rows"], _FailingObservations())


@pytest.mark.parametrize("mutation", ["missing", "reorder", "coordinated", "manual_pass", "reason"])
def test_safety_full_row_validator_rejects_coordinated_drift(mutation):
    state = gate.build_precondition_state()
    rows = copy.deepcopy(state["safety_rows"])
    if mutation == "missing":
        rows.pop()
    elif mutation == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "coordinated":
        rows[0]["required_status"] = rows[0]["observed_status"] = False
    elif mutation == "manual_pass":
        rows[0]["observed_status"] = False
        rows[0]["safety_passed"] = True
    else:
        rows[0]["blocking_reason"] = "DRIFT"
    assert not gate.validate_safety_rows(rows, state["execution"])


@pytest.mark.parametrize("section", gate.SECTION_NAMES)
def test_each_forced_section_failure_is_fail_closed(section):
    state = gate.build_precondition_state(forced_section_failures=(section,))
    assert state["sections"][section] is False
    assert state["all_checks_passed"] is False
    manifest = gate._manifest_payload(state, {name: "0" * 64 for name in gate.CSV_OUTPUTS})
    assert manifest["ready_for_real_provider_export_execution_smoke"] is False
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP
    assert len(manifest["current_domain_blocking_reasons"]) == 10
    assert len(state["issue_rows"]) == 2
    if section in {"source_boundary", "p6b0_predecessor", "p6a_binding", "authority_mapping"}:
        assert state["raw_open_count"] == state["raw_stat_count"] == state["raw_read_count"] == state["raw_hash_count"] == 0


def test_canonical_raw_telemetry_counts_are_exact_11():
    state = gate.build_precondition_state()
    assert len(state["raw_observations"]) == len(state["git_states"]) == 11
    assert state["raw_open_count"] == state["raw_stat_count"] == 11
    assert state["raw_read_count"] == state["raw_hash_count"] == 11
    assert all(
        observation.final_entry_stat_performed
        and observation.file_fd_opened
        and observation.fd_fstat_performed
        and observation.read_completed
        and observation.hash_completed
        for observation in state["raw_observations"]
    )


def test_failure_telemetry_missing_symlink_directory_partial_does_not_overclaim(tmp_path):
    missing_relative, missing_path = _raw_fixture(tmp_path, "missing.cif")
    missing_path.unlink()
    missing = gate.secure_hash_raw_source(missing_relative, repo_root=tmp_path)

    target_relative, target = _raw_fixture(tmp_path, "target.cif", b"sentinel")
    link = target.with_name("link.cif")
    link.symlink_to(target)
    final_symlink = gate.secure_hash_raw_source(
        target_relative.replace("target.cif", "link.cif"), repo_root=tmp_path,
        read_fn=lambda _fd, _size: pytest.fail("sentinel read"),
    )

    directory_relative, directory_path = _raw_fixture(tmp_path, "directory.cif")
    directory_path.unlink()
    directory_path.mkdir()
    directory = gate.secure_hash_raw_source(directory_relative, repo_root=tmp_path)

    partial_relative, _ = _raw_fixture(tmp_path, "partial.cif", b"abcdef")
    called = False
    def partial_read(fd, _size):
        nonlocal called
        if called:
            return b""
        called = True
        return os.read(fd, 1)
    partial = gate.secure_hash_raw_source(partial_relative, repo_root=tmp_path, read_fn=partial_read)

    assert all(not item.file_fd_opened and not item.hash_completed for item in (missing, final_symlink, directory))
    assert partial.file_fd_opened and partial.fd_fstat_performed
    assert not partial.read_completed and not partial.hash_completed


def test_safety_rows_derive_from_failure_telemetry():
    failure = gate.RawObservation(blocking_reason="RAW_SOURCE_MISSING")
    state = gate.build_precondition_state(raw_reader=lambda *_args, **_kwargs: failure)
    assert state["raw_open_count"] == state["raw_stat_count"] == 0
    assert state["raw_read_count"] == state["raw_hash_count"] == 0
    observed = {row["safety_item"]: row["observed_status"] for row in state["safety_rows"]}
    assert observed["exact_raw_path_component_opens"] is False
    assert observed["exact_raw_fd_fstat"] is False
    assert observed["exact_raw_fd_read"] is False
    assert observed["exact_raw_fd_sha256"] is False
    assert state["sections"]["safety"] is False


@pytest.mark.parametrize("section", [
    "source_boundary", "p6b0_predecessor", "p6a_binding", "authority_mapping",
])
def test_fail_state_manifest_authority_counts_do_not_overclaim(section):
    state = gate.build_precondition_state(forced_section_failures=(section,))
    manifest = gate._manifest_payload(state, {name: "0" * 64 for name in gate.CSV_OUTPUTS})
    assert manifest["historical_authority_row_count"] == 0
    assert manifest["expansion_authority_row_count"] == 0
    assert manifest["authority_binding_match_count"] == 0
    assert manifest["authority_conflict_count"] == 0
    assert manifest["raw_sha256_precondition_frozen_count"] == 0
    assert manifest["ready_for_real_provider_export_execution_smoke"] is False


def test_canonical_manifest_authority_counts_remain_3_8_11_0():
    state = gate.build_precondition_state()
    manifest = gate._manifest_payload(state, {name: "0" * 64 for name in gate.CSV_OUTPUTS})
    assert (
        manifest["historical_authority_row_count"],
        manifest["expansion_authority_row_count"],
        manifest["authority_binding_match_count"],
        manifest["authority_conflict_count"],
    ) == (3, 8, 11, 0)


@pytest.mark.parametrize("forced", [("unknown",), ("raw_access", "raw_access")])
def test_forced_section_names_reject_unknown_or_duplicate(forced):
    with pytest.raises(ValueError, match="FORCED_SECTION_FAILURES_INVALID"):
        gate.build_precondition_state(forced_section_failures=forced)


def test_runtime_git_state_drift_fails_matrix_and_readiness():
    provider = _git_provider(tracked=True, ignored=True)
    state = gate.build_precondition_state(git_provider=provider)
    assert state["passed_count"] == 0 and state["blocked_count"] == 11
    assert not state["sections"]["raw_access"]
    assert not state["all_checks_passed"]


def test_checker_rejects_runtime_git_state_drift(tmp_path, monkeypatch):
    checker = _load_checker()
    root = tmp_path / "outputs"
    gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1(root)
    drift = gate.build_precondition_state(git_provider=_git_provider(tracked=True, ignored=True))
    monkeypatch.setattr(checker.gate, "build_precondition_state", lambda **_kwargs: drift)
    with pytest.raises(AssertionError):
        checker.validate_outputs(root)


@pytest.mark.parametrize("filename", gate.CSV_OUTPUTS)
def test_checker_rejects_each_csv_disk_drift(tmp_path, filename):
    checker = _load_checker()
    root = tmp_path / "outputs"
    gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1(root)
    path = root / filename
    path.write_text(path.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker.validate_outputs(root)


def test_checker_rejects_manifest_overclaim_and_synchronized_csv_hash(tmp_path):
    checker = _load_checker()
    root = tmp_path / "outputs"
    gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1(root)
    matrix = root / gate.MATRIX_FILENAME
    matrix.write_text(matrix.read_text(encoding="utf-8").replace("passed", "blocked", 1), encoding="utf-8")
    manifest_path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_sha256"][gate.MATRIX_FILENAME] = hashlib.sha256(matrix.read_bytes()).hexdigest()
    manifest["all_checks_passed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker.validate_outputs(root)


def test_checker_rejects_coordinated_valid_stat_drift_with_synchronized_manifest_hash(tmp_path):
    checker = _load_checker()
    root = tmp_path / "outputs"
    gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1(root)
    matrix_path = root / gate.MATRIX_FILENAME
    with matrix_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        rows = list(reader)
    assert fieldnames is not None
    forged = "dev=1;ino=1;mode=1;nlink=1;size=1;mtime_ns=1;ctime_ns=1"
    rows[0]["pre_hash_stat_fingerprint"] = forged
    rows[0]["post_hash_stat_fingerprint"] = forged
    with matrix_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    manifest_path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_sha256"][gate.MATRIX_FILENAME] = hashlib.sha256(matrix_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker.validate_outputs(root)


def test_checker_rejects_false_manifest_authority_count_overclaim(tmp_path):
    checker = _load_checker()
    root = tmp_path / "outputs"
    gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1(root)
    manifest_path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["all_checks_passed"] = False
    manifest["real_raw_source_precondition_gate_passed"] = False
    manifest["ready_for_real_provider_export_execution_smoke"] = False
    manifest["validation_failures"] = ["source_boundary"]
    manifest["historical_authority_row_count"] = 3
    manifest["expansion_authority_row_count"] = 8
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker.validate_outputs(root)


@pytest.mark.parametrize("drift", ["missing", "extra", "symlink"])
def test_checker_rejects_output_set_and_symlink_drift(tmp_path, drift):
    checker = _load_checker()
    root = tmp_path / "outputs"
    gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1(root)
    target = root / gate.ISSUE_FILENAME
    if drift == "missing":
        target.unlink()
    elif drift == "extra":
        (root / "extra.csv").write_text("extra\n")
    else:
        target.unlink()
        target.symlink_to(root / gate.CONTRACT_FILENAME)
    with pytest.raises(AssertionError):
        checker.validate_outputs(root)


def test_checker_rejects_first_hash_and_source_constant_drift(tmp_path, monkeypatch):
    checker = _load_checker()
    root = tmp_path / "outputs"
    gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1(root)
    hashes = checker._output_hashes(root)
    hashes[gate.CONTRACT_FILENAME] = "0" * 64
    with pytest.raises(AssertionError):
        checker.validate_outputs(root, hashes)
    monkeypatch.setitem(gate.SOURCE_SHA256, str(gate.SOURCE_PATHS[0]), "0" * 64)
    with pytest.raises(AssertionError):
        checker._validated_source_snapshot()


def test_frozen_source_snapshot_binds_exact_nine_ordered_bytes_and_hashes():
    snapshot = _sources()
    assert snapshot.status == "passed" and snapshot.blocking_reason == ""
    assert snapshot.source_content_read_count == 9
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert all(
        record.sha256 == gate.SOURCE_SHA256[str(record.relative_path)]
        == hashlib.sha256(record.content_bytes).hexdigest()
        and record.size_bytes == len(record.content_bytes)
        and record.pre_stat_fingerprint == record.post_stat_fingerprint
        for record in snapshot.records
    )


def test_phase_a_structural_failure_prevents_every_source_content_read(tmp_path):
    reads = []
    snapshot = gate._build_frozen_source_snapshot(
        tmp_path,
        git_provider=_git_provider(tracked=True, ignored=True),
        read_fn=lambda *_args: reads.append(True) or b"",
    )
    assert snapshot.status == "blocked"
    assert snapshot.records == () and snapshot.source_content_read_count == 0
    assert reads == []


def test_frozen_csv_parse_survives_path_content_replacement(tmp_path):
    _materialize_source_fixture(tmp_path)
    snapshot = gate._build_frozen_source_snapshot(
        tmp_path, git_provider=_git_provider(tracked=True, ignored=True)
    )
    target = tmp_path / gate.P6A_BINDING_PATH
    target.write_bytes(b"replaced,after,snapshot\n")
    document = gate._read_frozen_csv(gate.P6A_BINDING_PATH, snapshot)
    assert document.status == "passed"
    assert document.header == gate.P6A_BINDING_HEADER and len(document.rows) == 11


def test_frozen_csv_parse_never_follows_post_snapshot_symlink(tmp_path):
    _materialize_source_fixture(tmp_path)
    snapshot = gate._build_frozen_source_snapshot(
        tmp_path, git_provider=_git_provider(tracked=True, ignored=True)
    )
    target = tmp_path / gate.P6A_BINDING_PATH
    sentinel = tmp_path / "sentinel.csv"
    sentinel.write_bytes(b"sentinel_must_not_be_parsed\n")
    target.unlink()
    target.symlink_to(sentinel)
    document = gate._read_frozen_csv(gate.P6A_BINDING_PATH, snapshot)
    assert document.status == "passed"
    assert document.header == gate.P6A_BINDING_HEADER and len(document.rows) == 11


def test_boundary_to_open_symlink_replacement_fails_before_content_read(tmp_path):
    _materialize_source_fixture(tmp_path)
    target = tmp_path / gate.SOURCE_PATHS[0]
    sentinel = tmp_path / "sentinel.txt"
    sentinel.write_bytes(b"sentinel_must_not_be_read")
    reads = []

    def replace_after_boundary():
        target.unlink()
        target.symlink_to(sentinel)

    snapshot = gate._build_frozen_source_snapshot(
        tmp_path,
        git_provider=_git_provider(tracked=True, ignored=True),
        read_fn=lambda *_args: reads.append(True) or b"",
        after_boundary_hook=replace_after_boundary,
    )
    assert snapshot.status == "blocked"
    assert snapshot.records == () and snapshot.source_content_read_count == 0
    assert reads == []


def test_source_modification_during_read_discards_partial_snapshot(tmp_path):
    _materialize_source_fixture(tmp_path)
    changed = False

    def modify_after_read(relative, _fd):
        nonlocal changed
        if not changed:
            changed = True
            (tmp_path / relative).write_bytes(b"changed during source read")

    snapshot = gate._build_frozen_source_snapshot(
        tmp_path,
        git_provider=_git_provider(tracked=True, ignored=True),
        after_source_read_hook=modify_after_read,
    )
    assert changed and snapshot.status == "blocked"
    assert snapshot.records == ()
    assert snapshot.blocking_reason == "SOURCE_CHANGED_DURING_READ"


def test_partial_source_read_is_never_accepted(tmp_path):
    _materialize_source_fixture(tmp_path)
    returned_byte = False

    def partial_read(fd, _size):
        nonlocal returned_byte
        if returned_byte:
            return b""
        returned_byte = True
        return os.read(fd, 1)

    snapshot = gate._build_frozen_source_snapshot(
        tmp_path,
        git_provider=_git_provider(tracked=True, ignored=True),
        read_fn=partial_read,
    )
    assert snapshot.status == "blocked" and snapshot.records == ()
    assert snapshot.blocking_reason == "SOURCE_PARTIAL_READ"


def test_wrong_source_sha_never_reaches_parse_or_raw_access(tmp_path, monkeypatch):
    _materialize_source_fixture(tmp_path)
    (tmp_path / gate.SOURCE_PATHS[0]).write_bytes(b"wrong source bytes")
    snapshot = gate._build_frozen_source_snapshot(
        tmp_path, git_provider=_git_provider(tracked=True, ignored=True)
    )
    assert snapshot.status == "blocked" and snapshot.records == ()
    assert snapshot.blocking_reason == "SOURCE_SHA256_MISMATCH"
    monkeypatch.setattr(gate, "_parse_csv_bytes", lambda _value: pytest.fail("source parse"))
    raw_calls = []
    state = gate.build_precondition_state(
        repo_root=tmp_path,
        source_snapshot=snapshot,
        raw_reader=lambda *_args, **_kwargs: raw_calls.append(True) or pytest.fail("raw access"),
        git_provider=_git_provider(tracked=False, ignored=True),
    )
    assert raw_calls == []
    assert state["source_content_read_count"] == 1
    assert state["source_snapshot_validated"] is False
    assert state["raw_open_count"] == state["raw_read_count"] == state["raw_hash_count"] == 0


def test_csv_parser_receives_the_exact_frozen_record_bytes(monkeypatch):
    snapshot = _sources()
    record = next(item for item in snapshot.records if item.relative_path == gate.P6A_BINDING_PATH)
    original = gate._parse_csv_bytes
    observed = []

    def parse(content_bytes):
        observed.append(content_bytes is record.content_bytes)
        return original(content_bytes)

    monkeypatch.setattr(gate, "_parse_csv_bytes", parse)
    assert gate._read_frozen_csv(gate.P6A_BINDING_PATH, snapshot).status == "passed"
    assert observed == [True]


def test_json_parser_receives_the_exact_frozen_record_bytes(monkeypatch):
    snapshot = _sources()
    record = next(item for item in snapshot.records if item.relative_path == gate.P6B0_MANIFEST_PATH)
    original = gate._parse_json_bytes
    observed = []

    def parse(content_bytes):
        observed.append(content_bytes is record.content_bytes)
        return original(content_bytes)

    monkeypatch.setattr(gate, "_parse_json_bytes", parse)
    assert gate._read_frozen_json(gate.P6B0_MANIFEST_PATH, snapshot).status == "passed"
    assert observed == [True]


def test_frozen_source_parse_and_state_use_explicit_repo_root(tmp_path, monkeypatch):
    root_a = tmp_path / "repo_a"
    root_b = tmp_path / "repo_b"
    _materialize_source_fixture(root_a)
    root_b.mkdir()
    snapshot = gate._build_frozen_source_snapshot(
        root_a, git_provider=_git_provider(tracked=True, ignored=True)
    )
    monkeypatch.setattr(gate, "REPO_ROOT", root_b)
    document = gate._read_frozen_csv(gate.P6A_BINDING_PATH, snapshot)
    assert document.status == "passed" and len(document.rows) == 11
    raw_roots = []

    def failed_raw(_relative, *, repo_root):
        raw_roots.append(repo_root)
        return gate.RawObservation(blocking_reason="SYNTHETIC_RAW_BLOCK")

    state = gate.build_precondition_state(
        repo_root=root_a,
        source_snapshot=snapshot,
        raw_reader=failed_raw,
        git_provider=_git_provider(tracked=False, ignored=True),
    )
    assert state["source_snapshot_validated"] is True
    assert state["source_content_read_count"] == 9
    assert raw_roots == [root_a] * 11


@pytest.mark.parametrize("failure", [False, True])
def test_source_fd_closure_on_success_and_failure(tmp_path, monkeypatch, failure):
    _materialize_source_fixture(tmp_path)
    if failure:
        (tmp_path / gate.SOURCE_PATHS[0]).write_bytes(b"hash mismatch")
    original_open = os.open
    original_close = os.close
    opened = []
    closed = []

    def tracked_open(*args, **kwargs):
        descriptor = original_open(*args, **kwargs)
        opened.append(descriptor)
        return descriptor

    def tracked_close(descriptor):
        closed.append(descriptor)
        return original_close(descriptor)

    monkeypatch.setattr(gate.os, "open", tracked_open)
    monkeypatch.setattr(gate.os, "close", tracked_close)
    snapshot = gate._build_frozen_source_snapshot(
        tmp_path, git_provider=_git_provider(tracked=True, ignored=True)
    )
    assert snapshot.status == ("blocked" if failure else "passed")
    assert opened and sorted(opened) == sorted(closed)


def _snapshot_with_record(
    snapshot: gate.FrozenSourceSnapshot,
    record: gate.FrozenSourceRecord,
) -> gate.FrozenSourceSnapshot:
    return replace(snapshot, records=(record, *snapshot.records[1:]))


def test_canonical_snapshot_is_bound_to_canonical_repo_root():
    snapshot = _sources()
    assert gate.validate_frozen_source_snapshot(snapshot, REPO_ROOT)
    assert snapshot.repo_root_identity == gate._repo_root_identity(REPO_ROOT)
    assert snapshot.repo_root_identity.lexical_absolute_path == os.path.abspath(os.fspath(REPO_ROOT))
    device, inode, mode = snapshot.repo_root_identity.stat_fingerprint
    assert device >= 0 and inode > 0 and gate.stat.S_ISDIR(mode)


def test_snapshot_from_repo_a_is_rejected_for_repo_b(tmp_path):
    root_a = tmp_path / "repo_a"
    root_b = tmp_path / "repo_b"
    _materialize_source_fixture(root_a)
    root_b.mkdir()
    snapshot = gate._build_frozen_source_snapshot(
        root_a, git_provider=_git_provider(tracked=True, ignored=True)
    )
    assert gate.validate_frozen_source_snapshot(snapshot, root_a)
    assert not gate.validate_frozen_source_snapshot(snapshot, root_b)


def test_mismatched_snapshot_root_blocks_parse_mapping_raw_and_git(tmp_path, monkeypatch):
    root_a = tmp_path / "repo_a"
    root_b = tmp_path / "repo_b"
    _materialize_source_fixture(root_a)
    root_b.mkdir()
    snapshot = gate._build_frozen_source_snapshot(
        root_a, git_provider=_git_provider(tracked=True, ignored=True)
    )
    monkeypatch.setattr(gate, "_parse_csv_bytes", lambda _value: pytest.fail("source parse"))
    raw_calls = []
    git_calls = []

    def git_provider(args, root):
        git_calls.append((tuple(args), root))
        return _result(1)

    state = gate.build_precondition_state(
        repo_root=root_b,
        source_snapshot=snapshot,
        raw_reader=lambda *_args, **_kwargs: raw_calls.append(True) or pytest.fail("raw access"),
        git_provider=git_provider,
    )
    manifest = gate._manifest_payload(
        state, {name: "0" * 64 for name in gate.CSV_OUTPUTS}
    )
    assert state["sections"]["source_boundary"] is False
    assert state["mapping"] == [] and raw_calls == [] and git_calls == []
    assert state["raw_open_count"] == state["raw_stat_count"] == 0
    assert state["raw_read_count"] == state["raw_hash_count"] == 0
    assert manifest["ready_for_real_provider_export_execution_smoke"] is False
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP


def test_run_mismatched_root_fails_closed_before_parse_raw_or_git(tmp_path, monkeypatch):
    root_a = tmp_path / "repo_a"
    root_b = tmp_path / "repo_b"
    _materialize_source_fixture(root_a)
    root_b.mkdir()
    snapshot = gate._build_frozen_source_snapshot(
        root_a, git_provider=_git_provider(tracked=True, ignored=True)
    )
    original_build = gate.build_precondition_state
    raw_calls = []
    git_calls = []

    def build(**kwargs):
        return original_build(
            **kwargs,
            raw_reader=lambda *_args, **_kw: raw_calls.append(True) or pytest.fail("raw access"),
            git_provider=lambda args, root: git_calls.append((tuple(args), root)) or _result(1),
        )

    monkeypatch.setattr(gate, "build_precondition_state", build)
    monkeypatch.setattr(gate, "_parse_csv_bytes", lambda _value: pytest.fail("source parse"))
    result = gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1(
        tmp_path / "outputs", repo_root=root_b, source_snapshot=snapshot
    )
    assert result["state"]["sections"]["source_boundary"] is False
    assert result["state"]["mapping"] == [] and raw_calls == [] and git_calls == []
    assert result["manifest"]["ready_for_real_provider_export_execution_smoke"] is False


@pytest.mark.parametrize("drift", ["lexical", "inode", "mode"])
def test_repo_root_identity_drift_or_forgery_is_rejected(drift):
    snapshot = _sources()
    identity = snapshot.repo_root_identity
    device, inode, mode = identity.stat_fingerprint
    if drift == "lexical":
        forged = replace(identity, lexical_absolute_path=identity.lexical_absolute_path + "-drift")
    elif drift == "inode":
        forged = replace(identity, stat_fingerprint=(device, inode + 1, mode))
    else:
        forged = replace(identity, stat_fingerprint=(device, inode, 1))
    assert not gate.validate_frozen_source_snapshot(
        replace(snapshot, repo_root_identity=forged), REPO_ROOT
    )


def test_repo_root_path_inode_replacement_is_rejected(tmp_path):
    root = tmp_path / "repo"
    moved = tmp_path / "moved"
    _materialize_source_fixture(root)
    snapshot = gate._build_frozen_source_snapshot(
        root, git_provider=_git_provider(tracked=True, ignored=True)
    )
    root.rename(moved)
    root.mkdir()
    assert not gate.validate_frozen_source_snapshot(snapshot, root)


@pytest.mark.parametrize("replacement", ["file", "symlink"])
def test_repo_root_file_or_symlink_is_rejected(tmp_path, replacement):
    snapshot = _sources()
    candidate = tmp_path / "candidate"
    if replacement == "file":
        candidate.write_bytes(b"not a directory")
    else:
        candidate.symlink_to(REPO_ROOT, target_is_directory=True)
    assert not gate.validate_frozen_source_snapshot(snapshot, candidate)


@pytest.mark.parametrize(
    "mutation",
    ["length", "non_int", "nonregular", "nlink", "inode", "stat_size", "record_size", "forged"],
)
def test_source_stat_semantic_forgery_is_rejected(mutation):
    snapshot = _sources()
    record = snapshot.records[0]
    fingerprint = list(record.pre_stat_fingerprint)
    record_size = record.size_bytes
    if mutation == "length":
        changed = tuple(fingerprint[:-1])
    elif mutation == "non_int":
        fingerprint[0] = True
        changed = tuple(fingerprint)
    elif mutation == "nonregular":
        fingerprint[2] = 1
        changed = tuple(fingerprint)
    elif mutation == "nlink":
        fingerprint[3] = 0
        changed = tuple(fingerprint)
    elif mutation == "inode":
        fingerprint[1] = 0
        changed = tuple(fingerprint)
    elif mutation == "stat_size":
        fingerprint[4] += 1
        changed = tuple(fingerprint)
    elif mutation == "record_size":
        changed = tuple(fingerprint)
        record_size += 1
    else:
        changed = (1, 1, 1, 1, record.size_bytes, 1, 1)
    forged_record = replace(
        record,
        size_bytes=record_size,
        pre_stat_fingerprint=changed,
        post_stat_fingerprint=changed,
    )
    assert not gate.validate_frozen_source_snapshot(
        _snapshot_with_record(snapshot, forged_record), REPO_ROOT
    )


def test_all_canonical_source_stat_fingerprints_are_semantically_valid():
    snapshot = _sources()
    assert all(
        gate._validate_source_stat_fingerprint(
            record.pre_stat_fingerprint, record.size_bytes
        )
        and gate._validate_source_stat_fingerprint(
            record.post_stat_fingerprint, record.size_bytes
        )
        for record in snapshot.records
    )


def test_explicit_root_overrides_global_drift_for_build_run_and_relative_output(tmp_path, monkeypatch):
    root_a = tmp_path / "repo_a"
    root_b = tmp_path / "repo_b"
    _materialize_source_fixture(root_a)
    root_b.mkdir()
    snapshot = gate._build_frozen_source_snapshot(
        root_a, git_provider=_git_provider(tracked=True, ignored=True)
    )
    original_build = gate.build_precondition_state
    raw_roots = []
    git_roots = []
    parse_count = 0
    original_parse = gate._parse_csv_bytes

    def parse(content_bytes):
        nonlocal parse_count
        parse_count += 1
        return original_parse(content_bytes)

    def raw_reader(_relative, *, repo_root):
        raw_roots.append(repo_root)
        return gate.RawObservation(blocking_reason="SYNTHETIC_RAW_BLOCK")

    def git_provider(args, root):
        git_roots.append(root)
        return _git_provider(tracked=False, ignored=True)(args, root)

    def build(**kwargs):
        return original_build(
            **kwargs, raw_reader=raw_reader, git_provider=git_provider
        )

    monkeypatch.setattr(gate, "REPO_ROOT", root_b)
    monkeypatch.setattr(gate, "_parse_csv_bytes", parse)
    monkeypatch.setattr(gate, "build_precondition_state", build)
    relative_output = Path("relative_outputs")
    result = gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1(
        relative_output, repo_root=root_a, source_snapshot=snapshot
    )
    output_root = root_a / relative_output
    assert output_root.is_dir() and not (root_b / relative_output).exists()
    assert {path.name for path in output_root.iterdir()} == set(gate.OUTPUT_FILES)
    assert parse_count == 3
    assert raw_roots == [root_a] * 11
    assert git_roots and set(git_roots) == {root_a}
    assert result["state"]["source_snapshot_validated"] is True
    assert all(str(root_a) not in path.read_text(encoding="utf-8") for path in output_root.iterdir())


@pytest.mark.parametrize("forgery", ["snapshot_root", "root_identity", "source_stat"])
def test_checker_rejects_snapshot_identity_and_stat_forgery(tmp_path, monkeypatch, forgery):
    checker = _load_checker()
    if forgery == "snapshot_root":
        root_a = tmp_path / "repo_a"
        _materialize_source_fixture(root_a)
        snapshot = gate._build_frozen_source_snapshot(
            root_a, git_provider=_git_provider(tracked=True, ignored=True)
        )
    else:
        snapshot = _sources()
    if forgery == "root_identity":
        identity = snapshot.repo_root_identity
        device, inode, mode = identity.stat_fingerprint
        snapshot = replace(
            snapshot,
            repo_root_identity=replace(
                identity, stat_fingerprint=(device, inode + 1, mode)
            ),
        )
    elif forgery == "source_stat":
        record = snapshot.records[0]
        forged = replace(
            record,
            pre_stat_fingerprint=(1, 1, 1, 1, record.size_bytes, 1, 1),
            post_stat_fingerprint=(1, 1, 1, 1, record.size_bytes, 1, 1),
        )
        snapshot = _snapshot_with_record(snapshot, forged)
    monkeypatch.setattr(checker.gate, "_build_frozen_source_snapshot", lambda _root: snapshot)
    with pytest.raises(AssertionError):
        checker._validated_source_snapshot()


def test_checker_stops_before_materialization_on_snapshot_root_mismatch(monkeypatch):
    checker = _load_checker()
    snapshot = _sources()
    identity = snapshot.repo_root_identity
    device, inode, mode = identity.stat_fingerprint
    mismatch = replace(
        snapshot,
        repo_root_identity=replace(
            identity, stat_fingerprint=(device, inode + 1, mode)
        ),
    )
    monkeypatch.setattr(checker.gate, "_build_frozen_source_snapshot", lambda _root: mismatch)
    monkeypatch.setattr(
        checker.gate,
        "run_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1",
        lambda **_kwargs: pytest.fail("materialization"),
    )
    with pytest.raises(AssertionError):
        checker.main()
