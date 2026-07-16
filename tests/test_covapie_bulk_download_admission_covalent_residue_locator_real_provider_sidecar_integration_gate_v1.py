from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from types import ModuleType

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_covalent_residue_locator_real_provider_sidecar_integration_gate
    as gate,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    REPO_ROOT
    / "scripts/check_covapie_bulk_download_admission_covalent_residue_locator_real_provider_sidecar_integration_gate_v1.py"
)


def _load_checker():
    spec = importlib.util.spec_from_file_location("p6d_checker", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _hashes(root: Path) -> dict[str, str]:
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in gate.OUTPUT_FILES}


def _replace_record(
    snapshot: gate.FrozenSourceSnapshot, path: Path, content: bytes,
) -> gate.FrozenSourceSnapshot:
    digest = hashlib.sha256(content).hexdigest()
    records = tuple(
        replace(record, expected_sha256=digest, observed_sha256=digest, content_bytes=content)
        if record.relative_path == path else record
        for record in snapshot.records
    )
    return gate.FrozenSourceSnapshot(records)


def _csv_bytes(header: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=list(header), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue().encode("utf-8")


def _mutate_csv_and_manifest(
    snapshot: gate.FrozenSourceSnapshot,
    csv_path: Path,
    manifest_path: Path,
    mutation,
) -> gate.FrozenSourceSnapshot:
    document = gate._csv_document(snapshot, csv_path)
    rows = [dict(row) for row in document.rows]
    mutation(rows)
    content = _csv_bytes(document.header, rows)
    updated = _replace_record(snapshot, csv_path, content)
    manifest = gate._json_document(updated, manifest_path)
    manifest["output_sha256"][csv_path.name] = hashlib.sha256(content).hexdigest()
    manifest_content = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    return _replace_record(updated, manifest_path, manifest_content)


@pytest.fixture(scope="module")
def snapshot() -> gate.FrozenSourceSnapshot:
    return gate.build_frozen_source_snapshot()


@pytest.fixture(scope="module")
def real_state() -> dict:
    state = gate.build_integration_state()
    assert state["all_checks_passed"] is True
    return state


def test_fixed_source_boundary_and_output_contract() -> None:
    assert len(gate.SOURCE_PATHS) == len(gate.SOURCE_SHA256) == 19
    assert tuple(gate.SOURCE_SHA256) == gate.SOURCE_PATHS
    assert len(set(gate.SOURCE_PATHS)) == 19
    assert gate.OVERLAY_COLUMNS == ("binding_row_id", *gate.PROVIDER_FIELDS)
    assert len(gate.OVERLAY_COLUMNS) == 6
    assert len(gate.EVIDENCE_COLUMNS) == 31
    assert gate.OUTPUT_FILES == (
        gate.CONTRACT_FILENAME, gate.OVERLAY_FILENAME, gate.EVIDENCE_FILENAME,
        gate.SAFETY_FILENAME, gate.ISSUE_FILENAME, gate.MANIFEST_FILENAME,
    )


def test_snapshot_is_exact_ordered_and_hash_valid(snapshot) -> None:
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert all(record.expected_sha256 == record.observed_sha256 for record in snapshot.records)


def test_source_failure_prevents_join_and_provider_recomputation(snapshot) -> None:
    record = snapshot.records[0]
    drift = replace(record, content_bytes=record.content_bytes + b"drift")
    bad = gate.FrozenSourceSnapshot((drift, *snapshot.records[1:]))
    state = gate.build_integration_state(source_snapshot=bad)
    assert state["source_ok"] is False
    assert state["keyed_join_count"] == 0
    assert state["p4_recomputation_count"] == 0
    assert state["overlay_rows"] == []
    assert state["all_checks_passed"] is False


def test_p3_direct_schema_validation(snapshot) -> None:
    passed, source = gate.validate_p3_predecessor(snapshot)
    assert passed
    assert len(source["fields"]) == 22
    assert len(source["rules"]) == 15
    assert len(source["contexts"]) == 18
    assert len(source["issues"]) == 10


@pytest.mark.parametrize(
    "mutation",
    (
        lambda rows: rows.pop(),
        lambda rows: rows.append(dict(rows[-1])),
        lambda rows: rows.__setitem__(18, {**rows[18], "field_name": "drift"}),
    ),
)
def test_p3_missing_duplicate_or_field_count_drift_fails(snapshot, mutation) -> None:
    bad = _mutate_csv_and_manifest(snapshot, gate.P3_FIELD_PATH, gate.P3_MANIFEST_PATH, mutation)
    assert gate.validate_p3_predecessor(bad)[0] is False


@pytest.mark.parametrize(
    "field,value",
    (("candidate_field_dependencies", "pdb_id"), ("blocking_reasons", "drift")),
)
def test_p3_admit_004_dependency_or_blocker_drift_fails(snapshot, field, value) -> None:
    def mutate(rows):
        target = next(row for row in rows if row["admission_rule_id"] == "ADMIT_004")
        target[field] = value

    bad = _mutate_csv_and_manifest(snapshot, gate.P3_RULE_PATH, gate.P3_MANIFEST_PATH, mutate)
    assert gate.validate_p3_predecessor(bad)[0] is False


def test_p6a_target_direct_validation(snapshot) -> None:
    passed, rows = gate.validate_p6a_target(snapshot)
    assert passed and len(rows) == 11
    assert [row["binding_row_id"] for row in rows] == [
        f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)
    ]
    assert len({row["sample_preparation_input_id"] for row in rows}) == 11
    assert len({(row["pdb_id"], row["ligand_comp_id"]) for row in rows}) == 11


def test_p6c_predecessor_direct_validation(snapshot) -> None:
    passed, source = gate.validate_p6c_predecessor(snapshot)
    assert passed
    assert len(source["sidecar"]) == len(source["evidence"]) == 11
    assert [row["issue_id"] for row in source["issues"]] == [
        gate.RESOLVED_PREDECESSOR_ISSUE_ID, gate.ACTIVE_PROVIDER_ISSUE_ID,
    ]


def test_p6c_manifest_overclaim_fails(snapshot) -> None:
    manifest = gate._json_document(snapshot, gate.P6C_MANIFEST_PATH)
    manifest["ready_for_training"] = True
    bad = _replace_record(
        snapshot, gate.P6C_MANIFEST_PATH,
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(),
    )
    assert gate.validate_p6c_predecessor(bad)[0] is False


def test_p6c_output_hash_drift_fails(snapshot) -> None:
    record = gate._record(snapshot, gate.P6C_SIDECAR_PATH)
    bad = _replace_record(snapshot, gate.P6C_SIDECAR_PATH, record.content_bytes + b"drift\n")
    assert gate.validate_p6c_predecessor(bad)[0] is False


def test_shared_process_preloaded_forbidden_modules_are_identity_preserved() -> None:
    missing = object()
    before = {
        name: sys.modules.get(name, missing)
        for name in gate.FORBIDDEN_RUNTIME_MODULE_NAMES
    }
    injected = {
        name: ModuleType(name)
        for name, module in before.items()
        if module is missing
    }
    try:
        sys.modules.update(injected)
        preloaded = {name: sys.modules[name] for name in gate.FORBIDDEN_RUNTIME_MODULE_NAMES}
        state = gate.build_integration_state()
        assert state["all_checks_passed"] is True
        assert state["runtime_forbidden_module_delta_ok"] is True
        assert state["runtime_forbidden_module_new_import_count"] == 0
        assert state["runtime_forbidden_module_replacement_count"] == 0
        assert state["runtime_forbidden_module_deletion_count"] == 0
        assert all(sys.modules[name] is module for name, module in preloaded.items())
        assert len(state["overlay_rows"]) == 11
        assert all(tuple(row) == gate.OVERLAY_COLUMNS for row in state["overlay_rows"])
    finally:
        for name, module in before.items():
            if module is missing:
                assert sys.modules.get(name) is injected[name]
                sys.modules.pop(name)
            else:
                assert sys.modules.get(name) is module


def test_runtime_loader_new_forbidden_import_fails_closed(monkeypatch) -> None:
    synthetic_name = "covalent_ext._p6d_forbidden_new_import_test"
    assert synthetic_name not in sys.modules
    monkeypatch.setattr(
        gate, "FORBIDDEN_RUNTIME_MODULE_NAMES",
        (*gate.FORBIDDEN_RUNTIME_MODULE_NAMES, synthetic_name),
    )
    p2, p4 = gate._load_runtime_modules()

    def malicious_loader():
        sys.modules[synthetic_name] = ModuleType(synthetic_name)
        return p2, p4

    try:
        state = gate.build_integration_state(module_loader=malicious_loader)
        assert state["runtime_forbidden_module_delta_ok"] is False
        assert state["runtime_forbidden_module_new_import_count"] == 1
        assert state["runtime_forbidden_module_replacement_count"] == 0
        assert state["p4_recomputation_count"] == 0
        assert state["overlay_rows"] == []
        assert state["all_checks_passed"] is False
    finally:
        sys.modules.pop(synthetic_name, None)


def test_runtime_loader_forbidden_replacement_fails_closed() -> None:
    target_name = gate.FORBIDDEN_RUNTIME_MODULE_NAMES[0]
    missing = object()
    before = sys.modules.get(target_name, missing)
    preloaded = before if before is not missing else ModuleType(target_name)
    p2, p4 = gate._load_runtime_modules()
    sys.modules[target_name] = preloaded

    def malicious_loader():
        sys.modules[target_name] = ModuleType(target_name)
        return p2, p4

    try:
        state = gate.build_integration_state(module_loader=malicious_loader)
        assert state["runtime_forbidden_module_delta_ok"] is False
        assert state["runtime_forbidden_module_new_import_count"] == 0
        assert state["runtime_forbidden_module_replacement_count"] == 1
        assert state["p4_recomputation_count"] == 0
        assert state["overlay_rows"] == []
        assert state["all_checks_passed"] is False
    finally:
        if before is missing:
            sys.modules.pop(target_name, None)
        else:
            sys.modules[target_name] = before


def test_runtime_loader_requests_exactly_p2_and_p4(monkeypatch) -> None:
    p2, p4 = gate._load_runtime_modules()
    modules = {
        gate.P2_RUNTIME_MODULE_NAME: p2,
        gate.P4_RUNTIME_MODULE_NAME: p4,
    }
    requested: list[str] = []

    def recording_import(name: str):
        requested.append(name)
        return modules[name]

    monkeypatch.setattr(gate.importlib, "import_module", recording_import)
    assert gate._load_runtime_modules() == (p2, p4)
    assert requested == [gate.P2_RUNTIME_MODULE_NAME, gate.P4_RUNTIME_MODULE_NAME]
    assert not set(requested).intersection(gate.FORBIDDEN_RUNTIME_MODULE_NAMES)


@pytest.mark.parametrize(
    "path,mutation",
    (
        (gate.P6C_SIDECAR_PATH, lambda rows: rows[0].update(provider_export_status="rejected")),
        (gate.P6C_SIDECAR_PATH, lambda rows: rows[0].update(observed_raw_sha256="0" * 64)),
        (gate.P6C_EVIDENCE_PATH, lambda rows: rows[0].update(evidence_audit_passed="false")),
    ),
)
def test_p6c_rejected_raw_sha_or_evidence_drift_fails(snapshot, path, mutation) -> None:
    bad = _mutate_csv_and_manifest(snapshot, path, gate.P6C_MANIFEST_PATH, mutation)
    assert gate.validate_p6c_predecessor(bad)[0] is False


def test_keyed_join_is_order_independent_but_target_ordered(real_state) -> None:
    targets = copy.deepcopy(real_state["targets"])
    sidecar = list(reversed(copy.deepcopy(real_state["p6c_source"]["sidecar"])))
    evidence = copy.deepcopy(real_state["p6c_source"]["evidence"])
    evidence[0], evidence[-1] = evidence[-1], evidence[0]
    joined, matches = gate.keyed_join_exact11(targets, sidecar, evidence)
    assert matches == len(joined) == 11
    assert [row[0]["binding_row_id"] for row in joined] == [
        f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)
    ]


@pytest.mark.parametrize("collection", ("targets", "sidecar", "evidence"))
@pytest.mark.parametrize("mode", ("row_count", "duplicate", "missing", "extra"))
def test_join_shape_duplicate_missing_extra_fail(real_state, collection, mode) -> None:
    targets = copy.deepcopy(real_state["targets"])
    sidecar = copy.deepcopy(real_state["p6c_source"]["sidecar"])
    evidence = copy.deepcopy(real_state["p6c_source"]["evidence"])
    rows = {"targets": targets, "sidecar": sidecar, "evidence": evidence}[collection]
    if mode in {"row_count", "missing"}:
        rows.pop()
    elif mode == "duplicate":
        rows[-1]["binding_row_id"] = rows[0]["binding_row_id"]
    else:
        extra = dict(rows[-1])
        extra["binding_row_id"] = "REAL_LOCATOR_BINDING_999999"
        rows.append(extra)
    assert gate.keyed_join_exact11(targets, sidecar, evidence) == ([], 0)


@pytest.mark.parametrize(
    "collection,field,value",
    (
        ("sidecar", "sample_execution_id", "drift"),
        ("sidecar", "conn_id", "drift"),
        ("evidence", "ligand_comp_id", "DRIFT"),
        ("evidence", "raw_target_relative_path", "drift"),
        ("sidecar", "matched_residue_atom_name", "CA"),
        ("sidecar", "observed_raw_sha256", "0" * 64),
    ),
)
def test_secondary_identity_path_ligand_conn_mismatch_fails(real_state, collection, field, value) -> None:
    targets = copy.deepcopy(real_state["targets"])
    sidecar = copy.deepcopy(real_state["p6c_source"]["sidecar"])
    evidence = copy.deepcopy(real_state["p6c_source"]["evidence"])
    {"targets": targets, "sidecar": sidecar, "evidence": evidence}[collection][0][field] = value
    assert gate.keyed_join_exact11(targets, sidecar, evidence) == ([], 0)


def _recompute_from_sidecar(real_state, sidecar):
    p2, p4 = gate._load_runtime_modules()
    joined, matches = gate.keyed_join_exact11(
        real_state["targets"], sidecar, real_state["p6c_source"]["evidence"],
    )
    if matches != 11:
        return [], [], 0, 0
    return gate.recompute_integration_rows(joined, p2, p4)


def test_unknown_empty_integrates_blocking(real_state) -> None:
    overlays, audits, recomputations, matches = _recompute_from_sidecar(
        real_state, copy.deepcopy(real_state["p6c_source"]["sidecar"]),
    )
    assert len(overlays) == len(audits) == recomputations == matches == 11
    assert all(row["integration_status"] == "integrated_blocking" for row in audits)


@pytest.mark.parametrize(
    "field,value",
    (
        (gate.PROVIDER_FIELDS[2], "A"),
        (gate.PROVIDER_FIELDS[1], "absent"),
        ("provider_export_blocking_reason", ""),
        (gate.PROVIDER_FIELDS[3], "drift"),
        (gate.PROVIDER_FIELDS[4], "0" * 64),
        ("matched_atom_site_id", "drift"),
        (gate.PROVIDER_FIELDS[0], "label"),
    ),
)
def test_insertion_provenance_payload_or_five_field_drift_fails(real_state, field, value) -> None:
    sidecar = copy.deepcopy(real_state["p6c_source"]["sidecar"])
    sidecar[0][field] = value
    overlays, audits, recomputations, matches = _recompute_from_sidecar(real_state, sidecar)
    assert overlays == audits == [] and recomputations == matches == 0


@pytest.mark.parametrize("exception", (TypeError("bad"), ValueError("bad")))
def test_p4_type_or_value_error_fails_closed(real_state, exception, monkeypatch) -> None:
    p2, p4 = gate._load_runtime_modules()

    def fail(**kwargs):
        raise exception

    monkeypatch.setattr(p4, "build_locator_provider_export_fields", fail)
    result = gate.recompute_integration_rows(real_state["joined_rows"], p2, p4)
    assert result == ([], [], 0, 0)


def test_overlay_exact_shape_order_and_values(real_state) -> None:
    rows = real_state["overlay_rows"]
    p2 = sys.modules[gate.P2_RUNTIME_MODULE_NAME]
    assert gate.validate_overlay_rows(rows, p2)
    assert len(rows) == 11
    assert all(tuple(row) == gate.OVERLAY_COLUMNS for row in rows)
    assert all(row[gate.PROVIDER_FIELDS[0]] == "auth" for row in rows)
    assert all(row[gate.PROVIDER_FIELDS[1]] == "unknown" for row in rows)
    assert all(row[gate.PROVIDER_FIELDS[2]] == "" for row in rows)


@pytest.mark.parametrize("mode", ("extra_field", "duplicate_id", "duplicate_source", "duplicate_sha", "reorder"))
def test_overlay_validator_rejects_drift(real_state, mode) -> None:
    rows = copy.deepcopy(real_state["overlay_rows"])
    if mode == "extra_field":
        rows[0]["extra"] = "x"
    elif mode == "duplicate_id":
        rows[1]["binding_row_id"] = rows[0]["binding_row_id"]
    elif mode == "duplicate_source":
        rows[1][gate.PROVIDER_FIELDS[3]] = rows[0][gate.PROVIDER_FIELDS[3]]
    elif mode == "duplicate_sha":
        rows[1][gate.PROVIDER_FIELDS[4]] = rows[0][gate.PROVIDER_FIELDS[4]]
    else:
        rows[0], rows[1] = rows[1], rows[0]
    assert not gate.validate_overlay_rows(rows, sys.modules[gate.P2_RUNTIME_MODULE_NAME])


def test_evidence_exact_11_integrated_blocking(real_state) -> None:
    assert gate.validate_evidence_rows(real_state["evidence_rows"])
    assert len(real_state["evidence_rows"]) == 11
    assert all(tuple(row) == gate.EVIDENCE_COLUMNS for row in real_state["evidence_rows"])


def test_contract_safety_and_active_issues(real_state) -> None:
    assert len(real_state["contract_rows"]) == len(gate.CONTRACT_SPECS)
    assert gate.validate_contract_rows(real_state["contract_rows"], real_state["observations"])
    assert all(row["safety_passed"] is True for row in real_state["safety_rows"])
    assert gate.validate_issue_rows(real_state["issue_rows"], real_state["p3_source"]["issues"])
    assert len(real_state["issue_rows"]) == 11
    assert all(row["issue_id"] != gate.RESOLVED_PREDECESSOR_ISSUE_ID for row in real_state["issue_rows"])


def test_exact_outputs_double_materialization_atomic_and_checker(tmp_path) -> None:
    checker = _load_checker()
    root = tmp_path / "outputs"
    first = gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_provider_sidecar_integration_gate_v1(root)
    first_hashes = checker._validate_result(first, root)
    first_bytes = {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    second = gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_provider_sidecar_integration_gate_v1(root)
    assert checker._validate_result(second, root) == first_hashes
    assert first_bytes == {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    assert not list(root.glob("*.tmp")) and not list(root.glob("*.part"))


@pytest.mark.parametrize("mode", ("missing", "extra", "symlink", "hash", "readiness"))
def test_checker_fails_closed_for_output_drift(tmp_path, mode) -> None:
    checker = _load_checker()
    root = tmp_path / "outputs"
    result = gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_provider_sidecar_integration_gate_v1(root)
    if mode == "missing":
        (root / gate.CONTRACT_FILENAME).unlink()
    elif mode == "extra":
        (root / "extra.csv").write_text("x\n", encoding="utf-8")
    elif mode == "symlink":
        target = root / gate.SAFETY_FILENAME
        target.unlink()
        target.symlink_to(root / gate.CONTRACT_FILENAME)
    elif mode == "hash":
        with (root / gate.OVERLAY_FILENAME).open("a", encoding="utf-8") as handle:
            handle.write("drift\n")
    else:
        path = root / gate.MANIFEST_FILENAME
        manifest = json.loads(path.read_text())
        manifest["ready_for_training"] = True
        path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises((AssertionError, csv.Error, json.JSONDecodeError)):
        checker._validate_result(result, root)


def test_manifest_readiness_and_resolved_issue(tmp_path) -> None:
    result = gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_provider_sidecar_integration_gate_v1(tmp_path)
    manifest = result["manifest"]
    assert manifest["real_provider_sidecar_integration_gate_passed"] is True
    assert manifest["real_provider_sidecar_integrated_into_additive_overlay"] is True
    assert manifest["resolved_predecessor_issue_ids"] == [gate.RESOLVED_PREDECESSOR_ISSUE_ID]
    assert manifest["candidate_records_materialized"] is False
    assert manifest["admission_records_modified"] is False
    assert manifest["real_samples_backfilled"] == 0
    assert manifest["ready_for_training"] is manifest["ready_to_train_now"] is False


def test_import_has_no_output_side_effect_and_no_forbidden_imports(tmp_path) -> None:
    code = (
        "import pathlib, sys; "
        "import covalent_ext.covapie_bulk_download_admission_covalent_residue_locator_real_provider_sidecar_integration_gate as g; "
        "print(sorted(p.name for p in pathlib.Path('.').iterdir())); "
        "print([n for n in g.FORBIDDEN_RUNTIME_MODULE_NAMES if n in sys.modules])"
    )
    result = subprocess.run(
        [sys.executable, "-B", "-c", code], cwd=tmp_path,
        env={"PYTHONPATH": str(REPO_ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
        text=True, capture_output=True, check=True,
    )
    assert result.stdout.splitlines() == ["[]", "[]"]
    assert result.stderr == ""


def test_production_and_checker_do_not_reference_raw_read_or_parser_calls() -> None:
    production = Path(gate.__file__).read_text(encoding="utf-8")
    checker = CHECKER_PATH.read_text(encoding="utf-8")
    assert "data/raw/" not in production
    assert "secure_read_expected_raw_source(" not in production
    assert "parse_mmcif" not in production
    assert "parser_provider_provenance_export_smoke as" not in production
    assert "data/raw/" not in checker


def test_checker_main_passes_for_committed_sources(tmp_path, monkeypatch) -> None:
    checker = _load_checker()
    monkeypatch.setattr(gate, "DEFAULT_OUTPUT_ROOT", tmp_path)
    assert checker.main() == 0
