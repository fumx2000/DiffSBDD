from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit as gate,
)


def _load_checker() -> object:
    path = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1.py"
    spec = importlib.util.spec_from_file_location("admit007_audit_checker", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _hashes(root: Path) -> dict[str, str]:
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in root.iterdir()}


def _refresh_manifest_hash(root: Path, name: str) -> None:
    manifest_path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_sha256"][name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _rewrite_csv(root: Path, name: str, mutate: object) -> None:
    path = root / name
    reader = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline=""))
    assert reader.fieldnames is not None
    rows = [dict(row) for row in reader]
    result = mutate(rows)  # type: ignore[operator]
    rows = rows if result is None else result
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=reader.fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(stream.getvalue(), encoding="utf-8")
    _refresh_manifest_hash(root, name)


def test_production_and_checker_imports_are_silent_and_side_effect_free(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    importlib.reload(gate)
    _load_checker()
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""
    assert not (tmp_path / gate.DEFAULT_OUTPUT_ROOT).exists()


def test_exact_six_outputs_are_byte_deterministic(tmp_path: Path) -> None:
    first = gate.run_covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1(tmp_path)
    hashes = _hashes(tmp_path)
    second = gate.run_covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1(tmp_path)
    assert first["manifest"] == second["manifest"] and hashes == _hashes(tmp_path)
    assert tuple(sorted(hashes)) == tuple(sorted(gate.OUTPUT_FILES))


def test_exact14_source_boundary_is_ordered_tracked_and_sha_frozen() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert len(snapshot.records) == 14
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert tuple(gate.SOURCE_SHA256) == gate.SOURCE_PATHS


def test_all_structural_checks_precede_first_content_read(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    original_structure = gate._structural_source_check
    original_git = gate._git
    original_read = Path.read_bytes

    def structure(path: Path, root: Path) -> bool:
        events.append(f"structure:{path}")
        return original_structure(path, root)

    def git(arguments: object, root: Path, *, text: bool = True) -> subprocess.CompletedProcess[object]:
        if list(arguments)[:1] == ["show"] and len(list(arguments)) == 2:
            events.append("content:git_show")
        return original_git(arguments, root, text=text)  # type: ignore[arg-type]

    def read(path: Path) -> bytes:
        if path in tuple(REPO_ROOT / item for item in gate.SOURCE_PATHS):
            events.append("content:filesystem")
        return original_read(path)

    monkeypatch.setattr(gate, "_structural_source_check", structure)
    monkeypatch.setattr(gate, "_git", git)
    monkeypatch.setattr(Path, "read_bytes", read)
    gate.build_frozen_source_snapshot()
    first_content = next(index for index, event in enumerate(events) if event.startswith("content:"))
    assert events[:first_content] == [f"structure:{path}" for path in gate.SOURCE_PATHS]


def test_non_descendant_base_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = gate._git

    def git(arguments: object, root: Path, *, text: bool = True) -> subprocess.CompletedProcess[object]:
        if list(arguments)[:2] == ["merge-base", "--is-ancestor"]:
            return subprocess.CompletedProcess([], 1, "" if text else b"", "" if text else b"")
        return original(arguments, root, text=text)  # type: ignore[arg-type]

    monkeypatch.setattr(gate, "_git", git)
    with pytest.raises(ValueError, match="not an ancestor"):
        gate.build_frozen_source_snapshot()


@pytest.mark.parametrize("failure", ["missing", "symlink"])
def test_missing_or_symlink_source_fails_before_byte_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    target = gate.SOURCE_PATHS[0]
    full = tmp_path / target
    full.parent.mkdir(parents=True)
    if failure == "symlink":
        victim = tmp_path / "victim"
        victim.write_text("victim", encoding="utf-8")
        full.symlink_to(victim)
    monkeypatch.setattr(gate, "_validate_expected_base_lineage", lambda *args, **kwargs: None)
    monkeypatch.setattr(gate, "_structural_source_check", lambda path, root: path != target)
    called = False

    def forbidden(*args: object, **kwargs: object) -> bytes:
        nonlocal called
        called = True
        raise AssertionError("content read forbidden")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    with pytest.raises(ValueError, match="structural"):
        gate.build_frozen_source_snapshot(tmp_path)
    assert called is False


def test_source_sha_tamper_snapshot_fails_closed() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    records = list(snapshot.records)
    item = records[0]
    records[0] = gate.FrozenSourceRecord(
        item.relative_path, item.expected_sha256, item.base_tree_sha256, "0" * 64, item.content_bytes
    )
    assert not gate.validate_frozen_source_snapshot(gate.FrozenSourceSnapshot(tuple(records)))


def test_committed_contracts_freeze_exact3_exact2_precedence_and_oracle() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    predecessor = gate._validate_predecessors(snapshot)
    assert predecessor["enum_truth_row_count"] == 37
    tree = gate._ast_document(snapshot, gate.ENUM_SOURCE_PATH)
    assert gate.INDEPENDENT_ORACLE in gate._top_level_functions(tree)
    assert gate.CANONICAL_ENUM_MEMBERS == (
        "explicit_structure_bond_record", "explicit_curated_covalent_annotation", "distance_only_inference"
    )
    assert gate.ALLOWED_COVALENT_EVIDENCE_CLASSES == gate.CANONICAL_ENUM_MEMBERS[:2]


def test_exact19_preconditions_are_ready_without_bulk_or_training_overclaim() -> None:
    rows = gate._precondition_rows()
    assert len(rows) == 19
    assert [row["precondition_id"] for row in rows] == [f"PRE_{index:03d}" for index in range(1, 20)]
    assert all(row["precondition_passed"] == "true" for row in rows)
    assert [row["semantics_complete"] for row in rows] == ["true"] * 15 + ["false"] * 4
    assert rows[17]["blocker_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    assert rows[18]["blocker_id"] == "FEATURE_SEMANTICS_AUDIT_REQUIRED"
    assert not any(row["blocker_id"] == "COVALENT_EVIDENCE_ENUM_UNRESOLVED" for row in rows)


def test_occurrence_inventory_covers_all_terms_and_source_roles() -> None:
    rows = gate._occurrence_rows(gate.build_frozen_source_snapshot())
    assert len(rows) == 280
    assert {row["matched_term"] for row in rows} == set(gate.MATCH_TERMS)
    assert len({(row["source_relative_path"], row["symbol_or_row_id"], row["matched_term"]) for row in rows}) == len(rows)
    assert any("historical lowercase" in row["semantic_statement"] for row in rows)
    assert any("current normative" in row["semantic_statement"] for row in rows)
    assert any("Exact6 runtime" in row["semantic_statement"] for row in rows)
    assert all(row["occurrence_passed"] == "true" for row in rows)


def test_real_provider_value_inventory_is_truthful_header_only(tmp_path: Path) -> None:
    assert gate._observed_value_rows() == ()
    gate.run_covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1(tmp_path)
    assert (tmp_path / gate.VALUE_FILENAME).read_text(encoding="utf-8").splitlines() == [",".join(gate.VALUE_COLUMNS)]


def test_exact11_issue_inventory_is_byte_identical_and_keeps_admit007_open() -> None:
    state = gate.build_audit_state()
    assert len(state["issue_rows"]) == 11
    assert state["issue_bytes"] == (REPO_ROOT / gate.RUNTIME_ISSUE_PATH).read_bytes()
    enum_issue = next(row for row in state["issue_rows"] if row["issue_id"] == "COVALENT_EVIDENCE_ENUM_UNRESOLVED")
    coverage = next(row for row in state["issue_rows"] if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assert enum_issue["status"] == "resolved"
    assert coverage["affected_rules"].split("|")[0] == "ADMIT_007"


def test_manifest_freezes_identity_outcomes_state_and_readiness(tmp_path: Path) -> None:
    manifest = gate.run_covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1(tmp_path)["manifest"]
    assert manifest["admission_rule_id"] == "ADMIT_007"
    assert manifest["formal_evaluator_blocked_reason"] == "DISTANCE_ONLY_INFERENCE_NOT_ADMISSIBLE"
    assert manifest["historical_registry_blocking_reason"] == "distance_only_inference_not_admissible"
    assert manifest["distance_only_outcome"] == "blocked"
    assert manifest["ready_for_admit_007_standalone_evaluator_interface_implementation"] is True
    assert manifest["admit_007_standalone_evaluator_implemented"] is False
    assert manifest["admit_007_registered_in_engine"] is False
    assert manifest["current_exact6_runtime_modified"] is False
    assert manifest["real_provider_enum_mapping_validated"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False and manifest["ready_to_train_now"] is False


def test_production_contains_no_evaluator_adapter_registry_or_oracle_call() -> None:
    tree = ast.parse(Path(gate.__file__).read_text(encoding="utf-8"))
    functions = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assigned = {
        target.id for node in tree.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
    }
    called = {
        node.func.id for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "evaluate_admit_007" not in functions
    assert "evaluate_all_rules" not in functions
    assert "EVALUATOR_REGISTRY" not in assigned
    assert gate.INDEPENDENT_ORACLE not in called


@pytest.mark.parametrize("kind", ["extra", "missing", "symlink"])
def test_output_missing_extra_and_symlink_fail_closed(tmp_path: Path, kind: str) -> None:
    root = tmp_path / "output"
    gate.run_covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1(root)
    checker = _load_checker()
    if kind == "extra":
        (root / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    elif kind == "missing":
        (root / gate.VALUE_FILENAME).unlink()
    else:
        victim = tmp_path / "victim"
        victim.write_text("unchanged", encoding="utf-8")
        (root / gate.VALUE_FILENAME).unlink()
        (root / gate.VALUE_FILENAME).symlink_to(victim)
    with pytest.raises((AssertionError, ValueError, FileNotFoundError)):
        checker._validate_disk(root, enforce_frozen_hashes=False)


def test_unexpected_output_is_not_deleted_and_symlink_victim_is_not_modified(tmp_path: Path) -> None:
    extra = tmp_path / "extra"
    extra.mkdir()
    unexpected = extra / "unexpected.txt"
    unexpected.write_text("keep", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected"):
        gate.run_covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1(extra)
    assert unexpected.read_text(encoding="utf-8") == "keep"
    unsafe = tmp_path / "unsafe"
    unsafe.mkdir()
    victim = tmp_path / "victim"
    victim.write_text("unchanged", encoding="utf-8")
    (unsafe / gate.SOURCE_BOUNDARY_FILENAME).symlink_to(victim)
    with pytest.raises(ValueError, match="unsafe"):
        gate.run_covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1(unsafe)
    assert victim.read_text(encoding="utf-8") == "unchanged"


@pytest.mark.parametrize(
    "case",
    [
        "enum_reopened", "pre006_incomplete", "distance_invalid", "admit006_reason",
        "lowercase_formal_reason", "explicit_blocked", "distance_passed",
        "context_canonical_cleared", "scalar_canonical_retained", "oracle_missing",
        "admit007_removed_from_coverage", "runtime_registered", "fake_provider_value",
        "raw_source_boundary", "source_sha_mismatch", "readiness_overclaim",
    ],
)
def test_semantic_tamper_with_refreshed_manifest_hash_fails_closed(tmp_path: Path, case: str) -> None:
    root = tmp_path / "output"
    gate.run_covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1(root)
    checker = _load_checker()
    if case == "enum_reopened":
        _rewrite_csv(root, gate.ISSUE_FILENAME, lambda rows: [
            {**row, "status": "open"} if row["issue_id"] == "COVALENT_EVIDENCE_ENUM_UNRESOLVED" else row for row in rows
        ])
    elif case == "pre006_incomplete":
        _rewrite_csv(root, gate.PRECONDITION_FILENAME, lambda rows: [
            {**row, "semantics_complete": "false"} if row["precondition_id"] == "PRE_006" else row for row in rows
        ])
    elif case in {"distance_invalid", "explicit_blocked", "distance_passed"}:
        replacements = {
            "distance_invalid": ("distance_only_inference=blocked", "distance_only_inference=invalid"),
            "explicit_blocked": ("=passed; distance_only", "=blocked; distance_only"),
            "distance_passed": ("distance_only_inference=blocked", "distance_only_inference=passed"),
        }
        old, new = replacements[case]
        _rewrite_csv(root, gate.PRECONDITION_FILENAME, lambda rows: [
            {**row, "observed_contract": row["observed_contract"].replace(old, new)} if row["precondition_id"] == "PRE_008" else row for row in rows
        ])
    elif case == "admit006_reason":
        _rewrite_csv(root, gate.PRECONDITION_FILENAME, lambda rows: [
            {**row, "observed_contract": row["observed_contract"].replace(gate.FORMAL_BLOCKED_REASON, "COVALENT_EVENT_EVIDENCE_NOT_EXPLICIT")} if row["precondition_id"] == "PRE_009" else row for row in rows
        ])
    elif case == "lowercase_formal_reason":
        path = root / gate.MANIFEST_FILENAME
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["formal_evaluator_blocked_reason"] = gate.HISTORICAL_REGISTRY_REASON
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    elif case in {"context_canonical_cleared", "scalar_canonical_retained"}:
        old, new = (
            ("context invalid retains canonical/pair", "context invalid clears canonical/pair")
            if case == "context_canonical_cleared"
            else ("scalar invalid clears canonical/pair", "scalar invalid retains canonical/pair")
        )
        field = "required_contract"
        _rewrite_csv(root, gate.PRECONDITION_FILENAME, lambda rows: [
            {**row, field: row[field].replace(old, new)} if row["precondition_id"] == "PRE_012" else row for row in rows
        ])
    elif case == "oracle_missing":
        def remove_oracle(rows: list[dict[str, str]]) -> list[dict[str, str]]:
            result = [row for row in rows if row["matched_term"] != gate.INDEPENDENT_ORACLE]
            for index, row in enumerate(result, 1):
                row["occurrence_order"] = str(index)
            return result
        _rewrite_csv(root, gate.OCCURRENCE_FILENAME, remove_oracle)
    elif case == "admit007_removed_from_coverage":
        _rewrite_csv(root, gate.ISSUE_FILENAME, lambda rows: [
            {**row, "affected_rules": row["affected_rules"].replace("ADMIT_007|", "")} if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE" else row for row in rows
        ])
    elif case == "runtime_registered":
        path = root / gate.MANIFEST_FILENAME
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["admit_007_registered_in_engine"] = True
        manifest["readiness"]["admit_007_registered_in_engine"] = True
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    elif case == "fake_provider_value":
        _rewrite_csv(root, gate.VALUE_FILENAME, lambda rows: [{column: ("1" if column == "value_order" else "distance_only_inference" if column == "observed_value" else "true" if column in ("real_provider_value", "value_inventory_passed") else "") for column in gate.VALUE_COLUMNS}])
    elif case in {"raw_source_boundary", "source_sha_mismatch"}:
        def source_mutation(rows: list[dict[str, str]]) -> None:
            if case == "raw_source_boundary":
                rows[0]["source_relative_path"] = "data/raw/forbidden.cif"
            else:
                rows[0]["filesystem_sha256"] = "0" * 64
        _rewrite_csv(root, gate.SOURCE_BOUNDARY_FILENAME, source_mutation)
    else:
        path = root / gate.MANIFEST_FILENAME
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["ready_for_bulk_download_now"] = True
        manifest["readiness"]["ready_for_bulk_download_now"] = True
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises((AssertionError, ValueError)):
        checker._validate_disk(root, enforce_frozen_hashes=False)


def test_materializer_preserves_all_frozen_sources_and_leaves_no_tmp_or_part(tmp_path: Path) -> None:
    before = {path: hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest() for path in gate.SOURCE_PATHS}
    gate.run_covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1(tmp_path)
    after = {path: hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest() for path in gate.SOURCE_PATHS}
    assert before == after == gate.SOURCE_SHA256
    assert not [path for path in tmp_path.iterdir() if path.suffix in (".tmp", ".part")]
