from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate as gate,
)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _checker_module():
    path = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate_v1.py"
    spec = importlib.util.spec_from_file_location("e1b_checker", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _materialize(tmp_path: Path) -> Path:
    root = tmp_path / "out"
    result = gate.run_covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate_v1(root)
    assert result["manifest"]["all_checks_passed"] is True
    return root


def _snapshot_with_replaced(snapshot, path: Path, content: bytes):
    records = tuple(
        gate.FrozenSourceRecord(
            record.relative_path, record.expected_sha256, record.observed_sha256,
            content if record.relative_path == path else record.content_bytes,
        )
        for record in snapshot.records
    )
    return gate.FrozenSourceSnapshot(records)


def test_exact12_order_structure_sha_and_direct_predecessors():
    snapshot = gate.build_frozen_source_snapshot()
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert len(snapshot.records) == 12
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert [record.observed_sha256 for record in snapshot.records] == [gate.SOURCE_SHA256[path] for path in gate.SOURCE_PATHS]
    assert gate._validate_p3(snapshot) is True
    assert gate._validate_e1a(snapshot) is True


def test_all_structural_checks_precede_first_content_read(monkeypatch):
    events: list[str] = []
    original_structure = gate._structural_source_check
    original_read = Path.read_bytes

    def structure(path, root):
        events.append(f"structure:{path}")
        return original_structure(path, root)

    def read(path):
        events.append(f"read:{path}")
        return original_read(path)

    monkeypatch.setattr(gate, "_structural_source_check", structure)
    monkeypatch.setattr(Path, "read_bytes", read)
    gate.build_frozen_source_snapshot()
    first_read = next(index for index, event in enumerate(events) if event.startswith("read:"))
    assert first_read == 12
    assert all(event.startswith("structure:") for event in events[:12])


def test_snapshot_hash_drift_fails_closed_with_zero_counts():
    snapshot = gate.build_frozen_source_snapshot()
    bad = _snapshot_with_replaced(snapshot, gate.P3_RULE_PATH, snapshot.records[0].content_bytes + b"drift")
    assert gate.validate_frozen_source_snapshot(bad) is False
    state = gate.build_integration_state(bad)
    assert state["all_checks_passed"] is False
    assert (state["integrated_rule_count"], state["integrated_field_count"], state["integrated_context_count"], state["active_issue_count"]) == (0, 0, 0, 0)


@pytest.mark.parametrize("mutation", ["missing", "symlink", "drift"])
def test_source_missing_symlink_and_hash_drift_fail_before_success_overlay(tmp_path, monkeypatch, mutation):
    snapshot = gate.build_frozen_source_snapshot()
    for record in snapshot.records:
        target = tmp_path / record.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(record.content_bytes)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--", *[path.as_posix() for path in gate.SOURCE_PATHS]], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=tmp_path, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    monkeypatch.setattr(gate, "EXPECTED_BASE_HEAD", head)
    target = tmp_path / gate.SOURCE_PATHS[0]
    if mutation == "missing":
        target.unlink()
    elif mutation == "symlink":
        target.unlink(); target.symlink_to(tmp_path / gate.SOURCE_PATHS[1])
    else:
        target.write_bytes(target.read_bytes() + b"drift")
    with pytest.raises(ValueError):
        gate.build_frozen_source_snapshot(tmp_path)


def test_exact_rule_overlay_and_thirteen_rows_unchanged():
    snapshot = gate.build_frozen_source_snapshot()
    state = gate.build_integration_state(snapshot)
    source = list(gate._csv_document(snapshot, gate.P3_RULE_PATH).rows)
    output = state["rule_rows"]
    source_map = {row["admission_rule_id"]: row for row in source}
    output_map = {row["admission_rule_id"]: row for row in output}
    assert len(output) == 15 and [row["admission_rule_id"] for row in output] == [row["admission_rule_id"] for row in source]
    assert output_map["ADMIT_004"] | {} == output_map["ADMIT_004"]
    assert output_map["ADMIT_004"]["semantics_complete"] == "false"
    assert output_map["ADMIT_004"]["deterministic_evaluation_possible_now"] == "false"
    assert output_map["ADMIT_004"]["blocking_reasons"] == gate.IDENTITY_ISSUE
    assert output_map["ADMIT_004"]["integration_reason"] == gate.PARTIAL_REASON
    assert output_map["ADMIT_005"]["semantics_complete"] == "true"
    assert output_map["ADMIT_005"]["deterministic_evaluation_possible_now"] == "true"
    assert output_map["ADMIT_005"]["implementation_disposition"] == "rule_logic_ready"
    assert output_map["ADMIT_005"]["blocking_reasons"] == ""
    assert output_map["ADMIT_005"]["integration_reason"] == gate.COMPLETE_REASON
    assert all(output_map[key] == source_map[key] for key in source_map if key not in {"ADMIT_004", "ADMIT_005"})
    for key in ("candidate_field_dependencies", "batch_context_dependencies", "evaluation_context_dependencies", "source_stage"):
        assert output_map["ADMIT_004"][key] == source_map["ADMIT_004"][key]
        assert output_map["ADMIT_005"][key] == source_map["ADMIT_005"][key]


def test_four_field_overlays_and_eighteen_rows_unchanged():
    snapshot = gate.build_frozen_source_snapshot()
    state = gate.build_integration_state(snapshot)
    source = list(gate._csv_document(snapshot, gate.P3_FIELD_PATH).rows)
    source_map = {row["field_name"]: row for row in source}
    output_map = {row["field_name"]: row for row in state["field_rows"]}
    assert len(output_map) == 22
    for name in gate.TARGET_FIELDS:
        row = output_map[name]
        assert all(row[column] == "true" for column in (
            "allowed_values_defined", "normalization_defined", "exact_validation_defined", "implementation_semantics_complete",
        ))
        assert row["semantics_evidence"] == gate.E1A_STAGE
        assert row["blocking_reasons"] == ""
        assert row["integration_source_stage"] == gate.E1A_STAGE
        assert row["integration_applied"] == "true"
        assert row["integration_reason"] == gate.FIELD_REASONS[name]
    assert all(output_map[name] == source_map[name] for name in source_map if name not in gate.TARGET_FIELDS)


def test_five_locator_rows_and_insertion_incomplete_row_do_not_drift():
    snapshot = gate.build_frozen_source_snapshot()
    state = gate.build_integration_state(snapshot)
    source = {row["field_name"]: row for row in gate._csv_document(snapshot, gate.P3_FIELD_PATH).rows}
    output = {row["field_name"]: row for row in state["field_rows"]}
    assert all(output[name] == source[name] for name in gate.LOCATOR_FIELDS)
    insertion = output["covalent_residue_insertion_code"]
    assert insertion["allowed_values_defined"] == "false"
    assert insertion["normalization_defined"] == "true"
    assert insertion["exact_validation_defined"] == "false"
    assert insertion["implementation_semantics_complete"] == "false"
    assert insertion["blocking_reasons"] == gate.IDENTITY_ISSUE


def test_identity_context_partial_only_and_other_seventeen_unchanged():
    snapshot = gate.build_frozen_source_snapshot()
    state = gate.build_integration_state(snapshot)
    source = list(gate._csv_document(snapshot, gate.P3_CONTEXT_PATH).rows)
    source_map = {row["context_item"]: row for row in source}
    output_map = {row["context_item"]: row for row in state["context_rows"]}
    target = output_map["covalent_residue_identity_contract"]
    assert target["deterministic_now"] == "false"
    assert target["deterministic_after_contract_freeze"] == "true"
    assert target["exact_contract_defined"] == "false"
    assert target["implementation_ready"] == "false"
    assert target["blocking_reasons"] == gate.IDENTITY_ISSUE
    assert target["integration_source_stage"] == gate.E1A_STAGE
    assert target["integration_reason"] == gate.PARTIAL_REASON
    assert all(output_map[name] == source_map[name] for name in source_map if name != "covalent_residue_identity_contract")


def test_issue_delete_redirect_order_and_other_nine_unchanged():
    snapshot = gate.build_frozen_source_snapshot()
    state = gate.build_integration_state(snapshot)
    source = list(gate._csv_document(snapshot, gate.E1A_ISSUE_PATH).rows)
    source_map = {row["issue_id"]: row for row in source}
    output = state["issue_rows"]
    output_map = {row["issue_id"]: row for row in output}
    assert len(output) == 10
    assert [row["issue_id"] for row in output] == [row["issue_id"] for row in source if row["issue_id"] != gate.ATOM_ISSUE]
    assert gate.ATOM_ISSUE not in output_map
    identity = output_map[gate.IDENTITY_ISSUE]
    assert identity["affected_fields"] == "covalent_residue_insertion_code"
    assert identity["affected_rules"] == "ADMIT_004"
    assert identity["integration_transition"] == "core_identity_and_atom_name_integrated_insertion_present_value_grammar_pending"
    assert identity["issue_origin"] == source_map[gate.IDENTITY_ISSUE]["issue_origin"]
    assert all(output_map[key] == source_map[key] for key in output_map if key != gate.IDENTITY_ISSUE)
    assert output_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["issue_count"] == "11"


def test_counts_exact11_and_no_unknown_to_absent_promotion():
    snapshot = gate.build_frozen_source_snapshot()
    state = gate.build_integration_state(snapshot)
    assert state["all_checks_passed"] is True
    assert (len(state["rule_rows"]), len(state["field_rows"]), len(state["context_rows"]), len(state["issue_rows"])) == (15, 22, 18, 10)
    assert sum(row["semantics_complete"] == "true" for row in state["rule_rows"]) == 6
    assert sum(row["implementation_semantics_complete"] == "true" for row in state["field_rows"]) == 11
    assert sum(row["implementation_ready"] == "true" for row in state["context_rows"]) == 8
    exact = gate._csv_document(snapshot, gate.E1A_EXACT11_PATH).rows
    assert len(exact) == 11
    assert all(row["insertion_state"] == "unknown" and row["insertion_value"] == "" for row in exact)
    assert all(row["insertion_blocks"] == "true" and row["effective_outcome"] == "blocked" for row in exact)
    assert all(row["reason"] == gate.UNKNOWN_REASON for row in exact)


def test_manifest_readiness_is_partial_and_fail_closed(tmp_path):
    root = _materialize(tmp_path)
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    true_keys = (
        "partial_successor_integration_applied", "core_residue_name_chain_index_semantics_integrated_into_effective_schema",
        "atom_name_semantics_integrated_into_effective_schema", "admit_005_rule_logic_ready",
        "ready_for_covalent_residue_insertion_present_value_grammar_design",
    )
    false_keys = (
        "residue_identity_semantics_integrated_into_effective_schema", "covalent_residue_identity_contract_fully_integrated",
        "admit_004_rule_logic_ready", "ready_for_admit_004_rule_logic_implementation", "admit_004_evaluator_implemented",
        "candidate_records_materialized", "ready_for_real_candidate_evaluation", "ready_for_bulk_download_now",
        "ready_for_training", "ready_to_train_now",
    )
    assert all(manifest[key] is True for key in true_keys)
    assert all(manifest[key] is False for key in false_keys)
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    assert manifest["resolved_issue_ids"] == [gate.ATOM_ISSUE]
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]


def test_safety_rows_are_exact_and_not_padding():
    rows = gate._safety_rows()
    assert [row["safety_item"] for row in rows] == [*gate.TRUE_SAFETY_ITEMS, *gate.FALSE_SAFETY_ITEMS]
    assert len(rows) == len(gate.TRUE_SAFETY_ITEMS) + len(gate.FALSE_SAFETY_ITEMS)
    assert all(row["safety_passed"] is True for row in rows)
    assert all(row["observed_executed"] is True for row in rows[:len(gate.TRUE_SAFETY_ITEMS)])
    assert all(row["observed_executed"] is False for row in rows[len(gate.TRUE_SAFETY_ITEMS):])


def test_deterministic_double_materialization(tmp_path):
    first = _materialize(tmp_path / "first")
    second = _materialize(tmp_path / "second")
    assert all((first / name).read_bytes() == (second / name).read_bytes() for name in gate.OUTPUT_FILES)
    assert not list(tmp_path.rglob("*.tmp")) and not list(tmp_path.rglob("*.part"))


@pytest.mark.parametrize("mutation", ["missing", "extra", "symlink", "hash", "overclaim"])
def test_checker_fails_closed_on_output_mutations(tmp_path, monkeypatch, mutation):
    root = _materialize(tmp_path)
    checker = _checker_module()
    monkeypatch.setattr(gate, "DEFAULT_OUTPUT_ROOT", root)
    if mutation == "missing":
        (root / gate.RULE_FILENAME).unlink()
    elif mutation == "extra":
        (root / "extra.csv").write_text("x\n", encoding="utf-8")
    elif mutation == "symlink":
        target = root / gate.RULE_FILENAME
        copy = root / "rule-copy"
        copy.write_bytes(target.read_bytes()); target.unlink(); target.symlink_to(copy)
    elif mutation == "hash":
        with (root / gate.RULE_FILENAME).open("a", encoding="utf-8") as handle:
            handle.write("drift\n")
    else:
        path = root / gate.MANIFEST_FILENAME
        value = json.loads(path.read_text(encoding="utf-8"))
        value["admit_004_rule_logic_ready"] = True
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises((AssertionError, FileNotFoundError)):
        checker.main()


def test_import_has_no_output_side_effects(capsys):
    path = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate.py"
    spec = importlib.util.spec_from_file_location("e1b_import_smoke", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""


def test_production_and_checker_import_only_standard_library():
    paths = (
        REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate.py",
        REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate_v1.py",
    )
    forbidden = {"torch", "numpy", "rdkit", "Bio", "gemmi", "dataset", "lightning_modules"}
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in (node.names if isinstance(node, ast.Import) else [ast.alias(name=node.module or "")])
        }
        assert imports.isdisjoint(forbidden)


def test_no_forbidden_generated_artifacts(tmp_path):
    root = _materialize(tmp_path)
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".tmp", ".part"}
    assert all(path.suffix not in forbidden for path in root.rglob("*") if path.is_file())
    assert all(path.stat().st_size < 1_000_000 for path in root.rglob("*") if path.is_file())
