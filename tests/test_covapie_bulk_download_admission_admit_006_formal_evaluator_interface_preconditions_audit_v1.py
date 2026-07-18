from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit as gate,
)


def _hashes(root: Path) -> dict[str, str]:
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in root.iterdir() if path.is_file()}


def _load_checker() -> object:
    path = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1.py"
    spec = importlib.util.spec_from_file_location("admit006_audit_checker", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_production_import_is_silent_and_has_no_materialization(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)
    importlib.reload(gate)
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""
    assert not (tmp_path / gate.DEFAULT_OUTPUT_ROOT).exists()


def test_checker_import_is_silent(capsys: pytest.CaptureFixture[str]) -> None:
    _load_checker()
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""


def test_exact_six_outputs_are_byte_deterministic(tmp_path: Path) -> None:
    first = gate.run_covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1(tmp_path)
    hashes = _hashes(tmp_path)
    second = gate.run_covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1(tmp_path)
    assert first["manifest"] == second["manifest"]
    assert hashes == _hashes(tmp_path)
    assert tuple(sorted(hashes)) == tuple(sorted(gate.OUTPUT_FILES))


def test_exact12_source_boundary_is_ordered_tracked_and_sha_frozen() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert len(snapshot.records) == 12
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert tuple(gate.SOURCE_SHA256) == gate.SOURCE_PATHS
    assert all(record.expected_sha256 == gate.SOURCE_SHA256[record.relative_path] for record in snapshot.records)


def test_all_structure_checks_precede_first_explicit_content_read(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    original_structure = gate._structural_source_check
    original_git = gate._git
    original_read_bytes = Path.read_bytes

    def structure(path: Path, root: Path) -> bool:
        events.append(f"structure:{path}")
        return original_structure(path, root)

    def git(arguments: object, root: Path, *, text: bool = True) -> subprocess.CompletedProcess[object]:
        if list(arguments)[:1] == ["show"] and len(list(arguments)) == 2:
            events.append("content:git_show")
        return original_git(arguments, root, text=text)  # type: ignore[arg-type]

    def read_bytes(path: Path) -> bytes:
        if path in tuple(REPO_ROOT / item for item in gate.SOURCE_PATHS):
            events.append("content:filesystem")
        return original_read_bytes(path)

    monkeypatch.setattr(gate, "_structural_source_check", structure)
    monkeypatch.setattr(gate, "_git", git)
    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    gate.build_frozen_source_snapshot()
    first_content = next(index for index, event in enumerate(events) if event.startswith("content:"))
    assert events[:first_content] == [f"structure:{path}" for path in gate.SOURCE_PATHS]


def test_non_descendant_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = gate._git

    def git(arguments: object, root: Path, *, text: bool = True) -> subprocess.CompletedProcess[object]:
        if list(arguments)[:2] == ["merge-base", "--is-ancestor"]:
            return subprocess.CompletedProcess([], 1, "" if text else b"", "" if text else b"")
        return original(arguments, root, text=text)  # type: ignore[arg-type]

    monkeypatch.setattr(gate, "_git", git)
    with pytest.raises(ValueError, match="not an ancestor"):
        gate.build_frozen_source_snapshot()


@pytest.mark.parametrize("failure", ["missing", "symlink"])
def test_missing_and_symlink_source_fail_before_content_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
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

    def forbidden(*args: object, **kwargs: object) -> object:
        nonlocal called
        called = True
        raise AssertionError("content read must not occur")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    with pytest.raises(ValueError, match="structural"):
        gate.build_frozen_source_snapshot(tmp_path)
    assert called is False


def test_hash_tamper_snapshot_fails_closed() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    records = list(snapshot.records)
    item = records[0]
    records[0] = gate.FrozenSourceRecord(item.relative_path, item.expected_sha256, item.base_tree_sha256, "0" * 64, item.content_bytes)
    assert not gate.validate_frozen_source_snapshot(gate.FrozenSourceSnapshot(tuple(records)))


def test_occurrence_inventory_is_complete_deduplicated_and_traceable() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    rows = gate._occurrence_rows(snapshot)
    assert len(rows) == 62
    keys = [(row["source_relative_path"], row["symbol_or_row_id"], row["matched_term"]) for row in rows]
    assert len(keys) == len(set(keys))
    assert all(row["source_relative_path"] in {path.as_posix() for path in gate.SOURCE_PATHS} for row in rows)
    assert all(row["source_sha256"] == gate.SOURCE_SHA256[Path(row["source_relative_path"])] for row in rows)
    assert all(row["occurrence_passed"] == "true" for row in rows)


def test_field_name_and_prose_are_not_enum_evidence() -> None:
    rows = gate._occurrence_rows(gate.build_frozen_source_snapshot())
    field_rows = [row for row in rows if row["matched_term"] == "covalent_event_evidence_source"]
    assert field_rows
    assert all(row["contains_concrete_value"] == "false" and row["concrete_value"] == "" for row in field_rows)
    assert any(row["semantic_statement"] == "historical value contract only; not an enum member" for row in rows)


def test_zero_value_inventory_is_valid_and_header_is_materialized(tmp_path: Path) -> None:
    assert gate._observed_value_rows() == ()
    gate.run_covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1(tmp_path)
    lines = (tmp_path / gate.VALUE_FILENAME).read_text(encoding="utf-8").splitlines()
    assert lines == [",".join(gate.VALUE_COLUMNS)]


def test_precondition_matrix_audits_all_nineteen_areas_without_overclaim() -> None:
    rows = gate._precondition_rows()
    assert len(rows) == 19
    assert [row["precondition_id"] for row in rows] == [f"PRE_{index:03d}" for index in range(1, 20)]
    assert all(row["precondition_passed"] == "true" for row in rows)
    assert sum(row["semantics_complete"] == "true" for row in rows) == 1
    assert next(row for row in rows if row["semantic_area"] == "allowed_enum")["semantics_complete"] == "false"
    assert next(row for row in rows if row["semantic_area"] == "standalone_evaluator_safety")["implementation_disposition"] == "blocked"


def test_predecessor_semantics_keep_shared_enum_blocker_open() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    predecessor = gate._validate_predecessors(snapshot)
    issues = predecessor["runtime_issue_rows"]
    assert len(issues) == 11
    blocker = next(row for row in issues if row["issue_id"] == "COVALENT_EVIDENCE_ENUM_UNRESOLVED")
    assert blocker["affected_rules"] == "ADMIT_006|ADMIT_007"
    assert blocker["severity"] == "blocking" and blocker["status"] == "open"


def test_current_runtime_is_exact5_and_admit006_is_not_implemented_or_registered() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    tree = gate._ast_document(snapshot, gate.RUNTIME_SOURCE_PATH)
    functions = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert gate._registry_keys(tree) == tuple(f"ADMIT_{index:03d}" for index in range(1, 6))
    assert "evaluate_admit_006" not in functions
    assert "evaluate_all_rules" not in functions


def test_manifest_truthfully_recommends_enum_design(tmp_path: Path) -> None:
    manifest = gate.run_covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1(tmp_path)["manifest"]
    assert manifest["canonical_evidence_enum_exists"] is False
    assert manifest["presence_only_nonempty_string_evaluator_safe"] is False
    assert manifest["ready_for_admit_006_standalone_evaluator_interface_implementation"] is False
    assert manifest["ready_for_covapie_covalent_event_evidence_source_enum_contract_design"] is True
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP


@pytest.mark.parametrize("key", [
    "admit_006_standalone_evaluator_implemented", "admit_006_registered_in_engine",
    "admit_007_registered_in_engine", "evaluate_all_rules_implemented", "real_candidate_evaluation",
    "exact11_real_rows_evaluated", "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
])
def test_forbidden_or_unready_manifest_claims_stay_false(tmp_path: Path, key: str) -> None:
    manifest = gate.run_covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1(tmp_path)["manifest"]
    assert manifest[key] is False


def test_issue_inventory_preserves_exact11_provider_coverage_and_cross_rule_boundaries() -> None:
    state = gate.build_audit_state()
    issues = state["issue_rows"]
    assert len(issues) == 11
    assert next(row for row in issues if row["issue_id"] == "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT")["issue_count"] == "11"
    coverage = next(row for row in issues if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assert coverage["affected_rules"].split("|") == [f"ADMIT_{index:03d}" for index in range(6, 16)]
    assert next(row for row in issues if row["issue_id"] == "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED")["status"] == "open"


def test_unexpected_output_entry_fails_closed_without_deletion(tmp_path: Path) -> None:
    unexpected = tmp_path / "unexpected.txt"
    unexpected.write_text("keep", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected"):
        gate.run_covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1(tmp_path)
    assert unexpected.read_text(encoding="utf-8") == "keep"


def test_symlink_output_victim_is_not_modified(tmp_path: Path) -> None:
    victim = tmp_path / "victim.txt"
    victim.write_text("unchanged", encoding="utf-8")
    output = tmp_path / "output"
    output.mkdir()
    (output / gate.SOURCE_BOUNDARY_FILENAME).symlink_to(victim)
    with pytest.raises(ValueError, match="unsafe"):
        gate.run_covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1(output)
    assert victim.read_text(encoding="utf-8") == "unchanged"


def test_symlink_output_root_fails_closed(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="real non-symlink"):
        gate.run_covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1(link)


def test_no_temporary_or_part_files_remain(tmp_path: Path) -> None:
    gate.run_covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1(tmp_path)
    assert not [path for path in tmp_path.iterdir() if path.suffix in (".tmp", ".part")]


def test_checker_rejects_tamper_and_overclaim(tmp_path: Path) -> None:
    gate.run_covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1(tmp_path)
    checker = _load_checker()
    checker._validate_disk(tmp_path, enforce_frozen_hashes=False)
    occurrence = tmp_path / gate.OCCURRENCE_FILENAME
    original = occurrence.read_bytes()
    occurrence.write_bytes(original + b"tamper")
    with pytest.raises(AssertionError):
        checker._validate_disk(tmp_path, enforce_frozen_hashes=False)
    occurrence.write_bytes(original)
    manifest_path = tmp_path / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["ready_for_admit_006_standalone_evaluator_interface_implementation"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker._validate_disk(tmp_path, enforce_frozen_hashes=False)


def test_production_source_contains_no_evaluator_or_registry_mutation() -> None:
    tree = ast.parse(Path(gate.__file__).read_text(encoding="utf-8"))
    functions = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert "evaluate_admit_006" not in functions
    assert "evaluate_all_rules" not in functions
    assigned = {target.id for node in tree.body if isinstance(node, ast.Assign) for target in node.targets if isinstance(target, ast.Name)}
    assert "EVALUATOR_REGISTRY" not in assigned


def test_materializer_does_not_mutate_frozen_sources(tmp_path: Path) -> None:
    before = {path: hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest() for path in gate.SOURCE_PATHS}
    gate.run_covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1(tmp_path)
    after = {path: hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest() for path in gate.SOURCE_PATHS}
    assert before == after == gate.SOURCE_SHA256
