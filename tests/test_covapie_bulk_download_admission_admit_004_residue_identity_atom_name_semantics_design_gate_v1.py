from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate
    as gate,
)


CHECKER_PATH = gate.REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate_v1.py"


def _snapshot_with_csv_rows(snapshot: gate.FrozenSourceSnapshot, path: Path, rows: list[dict[str, str]]) -> gate.FrozenSourceSnapshot:
    source = gate._csv_document(snapshot, path)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=source.header, lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    content = buffer.getvalue().encode()
    records = tuple(
        gate.FrozenSourceRecord(record.relative_path, record.expected_sha256, record.observed_sha256, content)
        if record.relative_path == path else record
        for record in snapshot.records
    )
    return gate.FrozenSourceSnapshot(records)


def _load_checker():
    spec = importlib.util.spec_from_file_location("e1a_checker_for_tests", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def test_exact22_source_boundary_order_and_sha() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert len(gate.SOURCE_PATHS) == len(gate.SOURCE_SHA256) == 22
    assert tuple(gate.SOURCE_SHA256) == gate.SOURCE_PATHS
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert all(record.observed_sha256 == gate.SOURCE_SHA256[record.relative_path] for record in snapshot.records)


def test_source_missing_symlink_and_hash_drift_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for source in gate.SOURCE_PATHS:
        target = tmp_path / source; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((gate.REPO_ROOT / source).read_bytes())
    monkeypatch.setattr(gate, "_structural_source_check", lambda path, root: (root / path).is_file() and not (root / path).is_symlink())
    missing = gate.SOURCE_PATHS[0]; (tmp_path / missing).unlink()
    with pytest.raises(ValueError, match="structural"): gate.build_frozen_source_snapshot(tmp_path)
    (tmp_path / missing).write_bytes((gate.REPO_ROOT / missing).read_bytes())
    symlink = gate.SOURCE_PATHS[1]; (tmp_path / symlink).unlink(); (tmp_path / symlink).symlink_to(tmp_path / missing)
    with pytest.raises(ValueError, match="structural"): gate.build_frozen_source_snapshot(tmp_path)
    (tmp_path / symlink).unlink(); (tmp_path / symlink).write_bytes((gate.REPO_ROOT / symlink).read_bytes() + b"drift")
    with pytest.raises(ValueError, match="SHA256"): gate.build_frozen_source_snapshot(tmp_path)


def test_all_structural_checks_precede_first_content_read(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[Path] = []
    original = gate._structural_source_check
    def check(path: Path, root: Path) -> bool:
        calls.append(path)
        return False if path == gate.SOURCE_PATHS[-1] else original(path, root)
    monkeypatch.setattr(gate, "_structural_source_check", check)
    with pytest.raises(ValueError, match="structural"): gate.build_frozen_source_snapshot()
    assert calls == list(gate.SOURCE_PATHS)


@pytest.mark.parametrize(("value", "valid", "canonical"), [
    ("CYS", True, "CYS"), ("cys", True, "CYS"), ("Cys", True, "CYS"),
    ("SER", True, "SER"), (" CYS", False, ""), ("CYS ", False, ""),
    ("CY S", False, ""), (".", False, ""), ("?", False, ""), ("", False, ""),
    (None, False, ""), (7, False, ""),
])
def test_residue_name_semantics(value: object, valid: bool, canonical: str) -> None:
    result = gate.normalize_covalent_residue_name(value)
    assert result.valid is valid and result.canonical_residue_name == canonical


@pytest.mark.parametrize(("value", "valid"), [("auth", True), ("label", True), ("AUTH", False), (" auth", False), ("auth ", False), (None, False)])
def test_namespace_semantics(value: object, valid: bool) -> None:
    assert gate.validate_covalent_residue_locator_namespace(value).valid is valid


def test_chain_index_lexical_preservation_and_no_coercion() -> None:
    assert gate.validate_covalent_residue_chain_id("01").value == "01"
    assert gate.validate_covalent_residue_index("0012").value == "0012"
    assert not gate.validate_covalent_residue_index(12).valid
    for value in ("", ".", "?", " 1", "1 ", "1\t2", "é"):
        assert not gate.validate_covalent_residue_index(value).valid


def test_selected_pair_same_namespace_mixed_and_mismatch() -> None:
    conflict = gate.validate_selected_residue_pair("auth", "A", "42", "A", "42", "L", "7")
    assert conflict.valid and conflict.auth_label_conflict_observed
    assert gate.validate_selected_residue_pair("label", "L", "7", "A", "42", "L", "7").valid
    assert not gate.validate_selected_residue_pair("auth", "A", "7", "A", "42", "L", "7").valid
    assert not gate.validate_selected_residue_pair("label", "A", "7", "A", "42", "L", "7").valid
    assert not gate.validate_selected_residue_pair("auth", "A", "42", "", "42", "L", "7").valid


@pytest.mark.parametrize(("value", "valid"), [
    ("SG", True), ("sg", False), ("Sg", False), (" SG", False), ("SG ", False),
    ("S", False), ("SULFUR", False), ("gamma-sulfur", False), (".", False),
    ("?", False), ("", False), (None, False),
])
def test_exact_sg_semantics(value: object, valid: bool) -> None:
    assert gate.validate_covalent_residue_atom_name(value).valid is valid


def test_provider_component_and_atom_conflicts_fail_closed() -> None:
    assert gate.validate_provider_identity_atom_evidence("CYS", "SG", matched_residue_atom_name="SG").valid
    component = gate.validate_provider_identity_atom_evidence("CYS", "SG", struct_conn_auth_comp_id="SER")
    atom = gate.validate_provider_identity_atom_evidence("CYS", "SG", atom_site_auth_atom_id="CB")
    assert (component.disposition, component.reason) == ("rejected", "PROVIDER_COMPONENT_EVIDENCE_CONFLICT")
    assert (atom.disposition, atom.reason) == ("rejected", "PROVIDER_ATOM_EVIDENCE_CONFLICT")


def test_provenance_source_id_matches_frozen_p2_contract_without_p2_import() -> None:
    assert gate.PROVENANCE_SOURCE_ID_PATTERN == r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$"
    valid_sha = "0" * 64
    for value in ("covapie:residue-locator:test", "covapie/path:source", "A" * 256):
        assert gate.validate_provenance_identity(value, valid_sha).valid
    for value in ("A" * 257, "bad source", ".", "?", "", None):
        assert not gate.validate_provenance_identity(value, valid_sha).valid
    assert not gate.validate_provenance_identity("covapie/path:source", "A" * 64).valid
    assert not gate.validate_provenance_identity("covapie/path:source", "0" * 63).valid


def test_truth_table_exact16_and_outcome_priority() -> None:
    rows = gate.build_truth_table_rows()
    assert len(rows) == 16 and all(row["truth_table_passed"] for row in rows)
    assert [row["case_id"] for row in rows] == [f"ADMIT004_TRUTH_{value:02d}" for value in range(1, 17)]
    assert gate.combine_effective_outcomes("passed", "blocked", "rejected", "invalid") == "invalid"
    with pytest.raises(ValueError): gate.combine_effective_outcomes("unknown")


def test_truth_case10_is_real_mixed_pair_and_distinct_from_case11() -> None:
    cases = {row["case_id"]: row for row in gate._truth_case_specs()}
    case10 = cases["ADMIT004_TRUTH_10"]
    case11 = cases["ADMIT004_TRUTH_11"]
    candidate10 = (case10["candidate_chain_id"], case10["candidate_residue_index"])
    auth10 = (case10["auth_chain_id"], case10["auth_residue_index"])
    label10 = (case10["label_chain_id"], case10["label_residue_index"])
    assert case10["locator_namespace"] == "auth"
    assert candidate10 == ("A", "7")
    assert auth10 == ("A", "42")
    assert label10 == ("L", "7")
    assert candidate10 != auth10 and candidate10 != label10
    candidate11 = (case11["candidate_chain_id"], case11["candidate_residue_index"])
    auth11 = (case11["auth_chain_id"], case11["auth_residue_index"])
    label11 = (case11["label_chain_id"], case11["label_residue_index"])
    assert candidate11 == ("B", "42")
    assert auth11 == label11 == ("A", "42")
    assert (candidate10, auth10, label10) != (candidate11, auth11, label11)


def test_admit004_admit005_separation_and_unknown_not_absent() -> None:
    base = dict(locator_namespace="auth", candidate_chain_id="A", candidate_residue_index="1",
                auth_chain_id="A", auth_residue_index="1", label_chain_id="A", label_residue_index="1",
                atom_name="SG", insertion_value="")
    non_cys = gate.evaluate_semantics_design(residue_name="SER", insertion_state="absent", **base)
    unknown = gate.evaluate_semantics_design(residue_name="CYS", insertion_state="unknown", **base)
    assert (non_cys["admit_004_outcome"], non_cys["admit_005_outcome"], non_cys["effective_outcome"]) == ("passed", "rejected", "rejected")
    assert (unknown["admit_004_outcome"], unknown["effective_outcome"], unknown["reason"]) == ("blocked", "blocked", gate.UNKNOWN_REASON)


def test_exact11_keyed_join_canonical_order_and_conflict_split() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    rows = gate.build_exact11_audit_rows(snapshot)
    binding_order = [row["binding_row_id"] for row in gate._csv_document(snapshot, gate.P6A_BINDING_PATH).rows]
    assert [row["binding_row_id"] for row in rows] == binding_order
    assert sum(row["auth_label_conflict_observed"] for row in rows) == 3
    assert sum(not row["auth_label_conflict_observed"] for row in rows) == 8
    assert all(row["audit_passed"] and row["effective_outcome"] == "blocked" for row in rows)


def test_exact11_join_does_not_depend_on_zip_order() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    overlay_rows = list(reversed(gate._csv_document(snapshot, gate.P6D_OVERLAY_PATH).rows))
    modified = _snapshot_with_csv_rows(snapshot, gate.P6D_OVERLAY_PATH, overlay_rows)
    rows = gate.build_exact11_audit_rows(modified)
    assert [row["binding_row_id"] for row in rows] == [row["binding_row_id"] for row in gate._csv_document(snapshot, gate.P6A_BINDING_PATH).rows]


def test_exact11_join_missing_extra_duplicate_fail_closed() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    rows = list(gate._csv_document(snapshot, gate.P6D_OVERLAY_PATH).rows)
    with pytest.raises(ValueError): gate.build_exact11_audit_rows(_snapshot_with_csv_rows(snapshot, gate.P6D_OVERLAY_PATH, rows[:-1]))
    extra = dict(rows[-1]); extra["binding_row_id"] = "EXTRA"
    with pytest.raises(ValueError): gate.build_exact11_audit_rows(_snapshot_with_csv_rows(snapshot, gate.P6D_OVERLAY_PATH, rows + [extra]))
    duplicate = list(rows); duplicate[-1] = dict(duplicate[0])
    with pytest.raises(ValueError): gate.build_exact11_audit_rows(_snapshot_with_csv_rows(snapshot, gate.P6D_OVERLAY_PATH, duplicate))


def test_issue_transitions_remain_open_and_blocking() -> None:
    state = gate.build_design_state(); assert state["all_checks_passed"]
    targets = {"COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED", "COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED"}
    assert len(state["issue_rows"]) == 11
    assert all(row["status"] == "open" and row["severity"] == "blocking" for row in state["issue_rows"])
    assert all(row["integration_transition"] == "design_frozen_pending_successor_integration" for row in state["issue_rows"] if row["issue_id"] in targets)
    assert all(row["integration_transition"] == "unchanged_open" for row in state["issue_rows"] if row["issue_id"] not in targets)


def test_deterministic_double_materialization_and_manifest_readiness(tmp_path: Path) -> None:
    first = gate.run_covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate_v1(tmp_path)
    first_bytes = {name: (tmp_path / name).read_bytes() for name in gate.OUTPUT_FILES}
    second = gate.run_covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate_v1(tmp_path)
    assert first_bytes == {name: (tmp_path / name).read_bytes() for name in gate.OUTPUT_FILES}
    manifest = second["manifest"]
    assert manifest["ready_for_residue_identity_atom_name_semantics_successor_integration"] is True
    assert manifest["admit_004_rule_logic_ready"] is False
    assert manifest["candidate_records_materialized"] is False
    assert manifest["ready_for_real_candidate_evaluation"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]


def test_checker_missing_extra_symlink_hash_and_overclaim_fail_closed(tmp_path: Path) -> None:
    checker = _load_checker()
    result = gate.run_covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate_v1(tmp_path)
    checker._validate_result(result, tmp_path)
    missing = tmp_path / gate.CONTRACT_FILENAME; content = missing.read_bytes(); missing.unlink()
    with pytest.raises(AssertionError): checker._validate_exact_output_set(tmp_path)
    missing.write_bytes(content); extra = tmp_path / "extra.csv"; extra.write_text("x\n")
    with pytest.raises(AssertionError): checker._validate_exact_output_set(tmp_path)
    extra.unlink(); missing.unlink(); missing.symlink_to(tmp_path / gate.TRUTH_FILENAME)
    with pytest.raises(AssertionError): checker._validate_exact_output_set(tmp_path)
    missing.unlink(); missing.write_bytes(content + b"drift")
    with pytest.raises(AssertionError): checker._validate_result(result, tmp_path)
    gate.run_covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate_v1(tmp_path)
    manifest_path = tmp_path / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text()); manifest["ready_for_training"] = True
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(AssertionError): checker._validate_result(result, tmp_path)


def test_import_has_no_stdout_stderr_side_effects() -> None:
    process = subprocess.run(
        [sys.executable, "-c", "import covalent_ext.covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate"],
        cwd=gate.REPO_ROOT, env={**os.environ, "PYTHONPATH": str(gate.REPO_ROOT / "src")},
        text=True, capture_output=True, check=False,
    )
    assert process.returncode == 0 and process.stdout == "" and process.stderr == ""


def test_production_imports_standard_library_only_and_no_forbidden_runtime_imports() -> None:
    source = Path(gate.__file__).read_text(encoding="utf-8")
    for forbidden in ("import torch", "import numpy", "import rdkit", "import Bio", "import gemmi",
                      "equivariant_diffusion", "lightning_modules", "dataset.py"):
        assert forbidden not in source
    assert "importlib" not in source
