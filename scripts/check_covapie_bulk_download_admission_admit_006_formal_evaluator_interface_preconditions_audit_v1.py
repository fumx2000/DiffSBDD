#!/usr/bin/env python3
"""Independently verify the ADMIT_006 preconditions audit outputs."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit as gate,
)


FROZEN_OUTPUT_SHA256 = {
    "covapie_admit_006_source_boundary_audit.csv": "89be06757e0d992ecd6ce9e7843bb9d36cebde9ff8d485a80ae7f1b6f2b84a3d",
    "covapie_admit_006_field_occurrence_inventory.csv": "bf7a705ffecb0dde8d7b62e6e6c15756614de358401d7055defb82711ce20660",
    "covapie_admit_006_observed_evidence_value_inventory.csv": "44698a4796be10cc317931df31da4829bccb23eaa95ed23d9797537f5a5feacc",
    "covapie_admit_006_evaluator_precondition_matrix.csv": "34073fad616472a9a8044cd21f498f33d535251e92b1ce7b549c1ad5dbf018ed",
    "covapie_admit_006_issue_readiness_inventory.csv": "7f815f3358ae3e53d296bc3ec0a129cd459184a76aa5169649b73fb1440e28bc",
    "covapie_admit_006_formal_evaluator_preconditions_manifest.json": "16b787061739dd0d68cfd3f66829a7690e802d1c0fa700d53155384b29c6dac5",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None
        return tuple(reader.fieldnames), list(reader)


def _assert_raises(callable_object: object, *args: object, **kwargs: object) -> None:
    try:
        callable_object(*args, **kwargs)  # type: ignore[operator]
    except (AssertionError, RuntimeError, ValueError):
        return
    raise AssertionError("negative path did not fail closed")


def _runtime_registry_keys() -> tuple[str, ...]:
    source = (REPO_ROOT / gate.RUNTIME_SOURCE_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source)
    keys = gate._registry_keys(tree)
    top_level = {
        node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "evaluate_admit_006" not in top_level
    assert "evaluate_all_rules" not in top_level
    return keys


def _validate_disk(root: Path, *, enforce_frozen_hashes: bool = True) -> dict[str, object]:
    expected = set(gate.OUTPUT_FILES)
    assert root.is_dir() and not root.is_symlink()
    assert {entry.name for entry in root.iterdir()} == expected
    assert all((root / name).is_file() and not (root / name).is_symlink() for name in expected)
    hashes = {name: _sha(root / name) for name in gate.OUTPUT_FILES}
    if enforce_frozen_hashes:
        assert hashes == FROZEN_OUTPUT_SHA256
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert type(manifest) is dict
    assert manifest["expected_base_commit"] == gate.EXPECTED_BASE_COMMIT
    assert manifest["expected_base_subject"] == gate.EXPECTED_BASE_SUBJECT
    assert manifest["source_input_count"] == 12
    assert manifest["source_input_paths"] == [path.as_posix() for path in gate.SOURCE_PATHS]
    assert manifest["source_input_sha256"] == {path.as_posix(): gate.SOURCE_SHA256[path] for path in gate.SOURCE_PATHS}
    assert manifest["output_files"] == list(gate.OUTPUT_FILES)
    assert manifest["output_file_count"] == 6
    assert manifest["output_sha256"] == {name: hashes[name] for name in gate.CSV_OUTPUTS}
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]
    boundary_header, boundary = _csv(root / gate.SOURCE_BOUNDARY_FILENAME)
    occurrence_header, occurrences = _csv(root / gate.OCCURRENCE_FILENAME)
    value_header, values = _csv(root / gate.VALUE_FILENAME)
    precondition_header, preconditions = _csv(root / gate.PRECONDITION_FILENAME)
    issue_header, issues = _csv(root / gate.ISSUE_FILENAME)
    assert boundary_header == gate.SOURCE_BOUNDARY_COLUMNS and len(boundary) == 12
    assert occurrence_header == gate.OCCURRENCE_COLUMNS and len(occurrences) == 62
    assert value_header == gate.VALUE_COLUMNS and values == []
    assert precondition_header == gate.PRECONDITION_COLUMNS and len(preconditions) == 19
    assert issue_header == gate.ISSUE_COLUMNS and len(issues) == 11
    assert tuple(row["source_relative_path"] for row in boundary) == tuple(path.as_posix() for path in gate.SOURCE_PATHS)
    assert all(row["source_boundary_passed"] == "true" for row in boundary)
    occurrence_keys = [(row["source_relative_path"], row["symbol_or_row_id"], row["matched_term"]) for row in occurrences]
    assert len(occurrence_keys) == len(set(occurrence_keys))
    assert all(row["contains_concrete_value"] == "false" and row["concrete_value"] == "" for row in occurrences)
    assert all(row["occurrence_passed"] == "true" for row in occurrences)
    assert any(row["field_role"] == "candidate_scalar|provider_metadata|context_item" for row in occurrences)
    assert all(row["precondition_passed"] == "true" for row in preconditions)
    assert sum(row["semantics_complete"] == "true" for row in preconditions) == 1
    blocker = next(row for row in issues if row["issue_id"] == "COVALENT_EVIDENCE_ENUM_UNRESOLVED")
    assert blocker["affected_fields"] == "covalent_event_evidence_source"
    assert blocker["affected_rules"] == "ADMIT_006|ADMIT_007"
    assert blocker["severity"] == "blocking" and blocker["status"] == "open"
    coverage = next(row for row in issues if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assert coverage["affected_rules"] == "ADMIT_006|ADMIT_007|ADMIT_008|ADMIT_009|ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"
    assert next(row for row in issues if row["issue_id"] == "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT")["issue_count"] == "11"
    assert next(row for row in issues if row["issue_id"] == "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED")["status"] == "open"
    assert _runtime_registry_keys() == tuple(f"ADMIT_{index:03d}" for index in range(1, 6))
    assert manifest["registered_rule_ids"] == [f"ADMIT_{index:03d}" for index in range(1, 6)]
    assert manifest["canonical_evidence_enum_exists"] is False
    assert manifest["observed_evidence_value_row_count"] == 0
    assert manifest["presence_only_nonempty_string_evaluator_safe"] is False
    assert manifest["covalent_evidence_enum_issue_status"] == "open"
    assert manifest["ready_for_covapie_covalent_event_evidence_source_enum_contract_design"] is True
    assert manifest["ready_for_admit_006_standalone_evaluator_interface_implementation"] is False
    assert manifest["admit_006_standalone_evaluator_implemented"] is False
    assert manifest["admit_006_registered_in_engine"] is False
    assert manifest["admit_007_registered_in_engine"] is False
    assert manifest["evaluate_all_rules_implemented"] is False
    assert manifest["real_candidate_evaluation"] is False
    assert manifest["exact11_real_rows_evaluated"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False and manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    assert manifest["all_checks_passed"] is True
    serialized = json.dumps(manifest, sort_keys=True)
    assert "timestamp" not in serialized.lower() and "/home/" not in serialized
    return manifest


def _negative_source_checks(snapshot: gate.FrozenSourceSnapshot) -> None:
    records = list(snapshot.records)
    original = records[0]
    records[0] = gate.FrozenSourceRecord(
        original.relative_path, original.expected_sha256, original.base_tree_sha256,
        "0" * 64, original.content_bytes,
    )
    assert not gate.validate_frozen_source_snapshot(gate.FrozenSourceSnapshot(tuple(records)))
    original_git = gate._git
    try:
        def non_descendant(arguments: object, repo_root: Path, *, text: bool = True) -> subprocess.CompletedProcess[object]:
            if list(arguments)[:2] == ["merge-base", "--is-ancestor"]:
                return subprocess.CompletedProcess([], 1, "" if text else b"", "" if text else b"")
            return original_git(arguments, repo_root, text=text)  # type: ignore[arg-type]
        gate._git = non_descendant  # type: ignore[assignment]
        _assert_raises(gate._validate_expected_base_lineage, REPO_ROOT)
    finally:
        gate._git = original_git  # type: ignore[assignment]


def _negative_output_checks(root: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="covapie_admit006_checker_") as temporary:
        temp = Path(temporary)
        copied = temp / "copy"
        shutil.copytree(root, copied)
        with (copied / gate.OCCURRENCE_FILENAME).open("ab") as handle:
            handle.write(b"tamper")
        _assert_raises(_validate_disk, copied)
        copied_extra = temp / "extra"
        shutil.copytree(root, copied_extra)
        (copied_extra / "unexpected.txt").write_text("unexpected", encoding="utf-8")
        _assert_raises(_validate_disk, copied_extra)
        copied_overclaim = temp / "overclaim"
        shutil.copytree(root, copied_overclaim)
        manifest_path = copied_overclaim / gate.MANIFEST_FILENAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["ready_for_admit_006_standalone_evaluator_interface_implementation"] = True
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _assert_raises(_validate_disk, copied_overclaim, enforce_frozen_hashes=False)
        unsafe = temp / "unsafe"
        unsafe.mkdir()
        victim = temp / "victim.txt"
        victim.write_text("unchanged", encoding="utf-8")
        (unsafe / gate.SOURCE_BOUNDARY_FILENAME).symlink_to(victim)
        _assert_raises(
            gate.run_covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1,
            unsafe,
        )
        assert victim.read_text(encoding="utf-8") == "unchanged"


def main() -> int:
    root = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    first = gate.run_covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1(root)
    first_hashes = {name: _sha(root / name) for name in gate.OUTPUT_FILES}
    second = gate.run_covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1(root)
    second_hashes = {name: _sha(root / name) for name in gate.OUTPUT_FILES}
    assert first["manifest"] == second["manifest"] and first_hashes == second_hashes
    manifest = _validate_disk(root)
    snapshot = gate.build_frozen_source_snapshot()
    _negative_source_checks(snapshot)
    _negative_output_checks(root)
    assert manifest["field_occurrence_row_count"] == 62
    assert manifest["observed_evidence_value_row_count"] == 0
    assert manifest["canonical_evidence_enum_exists"] is False
    assert manifest["presence_only_nonempty_string_evaluator_safe"] is False
    assert manifest["ready_for_admit_006_standalone_evaluator_interface_implementation"] is False
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    print(f"stage={gate.STAGE}")
    print("all_checks_passed=true")
    print("source_boundary_exact12=true")
    print("field_occurrence_row_count=62")
    print("observed_evidence_value_row_count=0")
    print("canonical_evidence_enum_exists=false")
    print("presence_only_nonempty_string_evaluator_safe=false")
    print("ready_for_admit_006_standalone_evaluator_interface_implementation=false")
    print(f"recommended_next_step={gate.RECOMMENDED_NEXT_STEP}")
    print("outputs_byte_identical=true")
    print("covapie_admit_006_formal_evaluator_interface_preconditions_audit_v1_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
