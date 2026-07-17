#!/usr/bin/env python3
"""Check the CovaPIE minimal unified ADMIT_004 dispatch shell v1."""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import inspect
import io
import json
import os
import shutil
import stat
import sys
import tempfile
from collections import Counter
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004 as shell,
)


def _csv_rows(content: bytes, columns: tuple[str, ...]) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(
        io.StringIO(content.decode("utf-8", errors="strict"), newline="")
    )
    if tuple(reader.fieldnames or ()) != columns:
        raise AssertionError("output CSV header mismatch")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != columns or any(value is None for value in row.values()) for row in rows):
        raise AssertionError("output CSV row mismatch")
    return rows


def _expected_materialization() -> tuple[dict[str, bytes], dict[str, Any]]:
    state = shell.build_phase2_state()
    assert state["all_checks_passed"] is True
    payloads, manifest = shell._payloads(state)
    assert tuple(payloads) == shell.OUTPUT_FILES
    assert len(payloads) == 6
    return payloads, manifest


def validate_output_root(
    root: Path, expected_payloads: Mapping[str, bytes], expected_manifest: Mapping[str, Any]
) -> dict[str, str]:
    metadata = os.lstat(root)
    assert stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
    entries = tuple(root.iterdir())
    assert {entry.name for entry in entries} == set(shell.OUTPUT_FILES)
    actual_bytes: dict[str, bytes] = {}
    for name in shell.OUTPUT_FILES:
        path = root / name
        entry_metadata = os.lstat(path)
        assert stat.S_ISREG(entry_metadata.st_mode)
        assert not stat.S_ISLNK(entry_metadata.st_mode)
        actual_bytes[name] = path.read_bytes()
        assert actual_bytes[name] == expected_payloads[name]
    actual_manifest = json.loads(
        actual_bytes[shell.MANIFEST_FILENAME].decode("utf-8", errors="strict")
    )
    assert type(actual_manifest) is dict
    assert actual_manifest == expected_manifest
    assert set(actual_manifest["output_sha256"]) == set(shell.CSV_OUTPUTS)
    for name in shell.CSV_OUTPUTS:
        assert actual_manifest["output_sha256"][name] == hashlib.sha256(
            actual_bytes[name]
        ).hexdigest()
    for item in shell.TRUE_READINESS:
        assert actual_manifest["readiness"][item] is True
        assert actual_manifest[item] is True
    for item in shell.FALSE_READINESS:
        assert actual_manifest["readiness"][item] is False
        assert actual_manifest[item] is False
    assert actual_manifest["unified_rule_engine_implemented"] is False
    assert actual_manifest["legacy_evaluator_adapters_implemented"] is False
    assert actual_manifest["combined_candidate_verdict_implemented"] is False
    assert actual_manifest["cross_rule_precedence_frozen"] is False
    assert actual_manifest["real_candidate_evaluation"] is False
    assert actual_manifest["exact11_real_rows_evaluated"] is False
    assert actual_manifest["ready_for_bulk_download_now"] is False
    assert actual_manifest["ready_for_training"] is False
    assert actual_manifest["ready_to_train_now"] is False
    assert not any(
        entry.name.endswith((".tmp", ".part")) for entry in root.iterdir()
    )
    return {
        name: hashlib.sha256(content).hexdigest()
        for name, content in actual_bytes.items()
    }


def _assert_output_failure_modes(
    expected_payloads: Mapping[str, bytes], expected_manifest: Mapping[str, Any]
) -> None:
    with tempfile.TemporaryDirectory(prefix="covapie_phase2_output_failures_") as temporary:
        base = Path(temporary)

        def fresh(name: str) -> Path:
            root = base / name
            root.mkdir()
            for filename, content in expected_payloads.items():
                (root / filename).write_bytes(content)
            return root

        missing = fresh("missing")
        (missing / shell.CONTRACT_FILENAME).unlink()
        try:
            validate_output_root(missing, expected_payloads, expected_manifest)
        except (AssertionError, FileNotFoundError):
            pass
        else:
            raise AssertionError("missing output did not fail closed")

        extra = fresh("extra")
        (extra / "unexpected.csv").write_text("unexpected\n", encoding="utf-8")
        try:
            validate_output_root(extra, expected_payloads, expected_manifest)
        except AssertionError:
            pass
        else:
            raise AssertionError("extra output did not fail closed")

        corrupt = fresh("corrupt")
        (corrupt / shell.TRUTH_FILENAME).write_bytes(b"manifest boolean is not evidence\n")
        try:
            validate_output_root(corrupt, expected_payloads, expected_manifest)
        except AssertionError:
            pass
        else:
            raise AssertionError("corrupt output did not fail closed")

        overclaim = fresh("overclaim")
        manifest_path = overclaim / shell.MANIFEST_FILENAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["ready_for_training"] = True
        manifest["readiness"]["ready_for_training"] = True
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        try:
            validate_output_root(overclaim, expected_payloads, expected_manifest)
        except AssertionError:
            pass
        else:
            raise AssertionError("manifest readiness overclaim did not fail closed")

        symlinked = fresh("symlinked")
        target = base / "unchanged_target"
        target.write_bytes(b"unchanged")
        link = symlinked / shell.SAFETY_FILENAME
        link.unlink()
        link.symlink_to(target)
        try:
            validate_output_root(symlinked, expected_payloads, expected_manifest)
        except AssertionError:
            pass
        else:
            raise AssertionError("symlink output did not fail closed")
        assert target.read_bytes() == b"unchanged"


def _assert_materializer_safety(
    expected_payloads: Mapping[str, bytes], expected_manifest: Mapping[str, Any]
) -> None:
    with tempfile.TemporaryDirectory(prefix="covapie_phase2_materializer_") as temporary:
        base = Path(temporary)
        first = base / "first"
        second = base / "second"
        shell.run_covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1(
            first
        )
        shell.run_covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1(
            second
        )
        first_hashes = validate_output_root(first, expected_payloads, expected_manifest)
        second_hashes = validate_output_root(second, expected_payloads, expected_manifest)
        assert first_hashes == second_hashes
        assert all(
            (first / name).read_bytes() == (second / name).read_bytes()
            for name in shell.OUTPUT_FILES
        )

        victim = base / "victim"
        victim.write_bytes(b"victim-must-remain-unchanged")
        unsafe = base / "unsafe"
        unsafe.mkdir()
        (unsafe / shell.CONTRACT_FILENAME).symlink_to(victim)
        try:
            shell.run_covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1(
                unsafe
            )
        except ValueError:
            pass
        else:
            raise AssertionError("materializer symlink victim did not fail closed")
        assert victim.read_bytes() == b"victim-must-remain-unchanged"
        assert {entry.name for entry in unsafe.iterdir()} == {shell.CONTRACT_FILENAME}
        assert not tuple(base.rglob("*.tmp"))
        assert not tuple(base.rglob("*.part"))


def _assert_runtime_contract(state: Mapping[str, Any]) -> None:
    assert dataclasses.is_dataclass(shell.UnifiedAdmissionRuleEvaluation)
    assert shell.UnifiedAdmissionRuleEvaluation.__dataclass_params__.frozen is True
    assert tuple(
        field.name for field in dataclasses.fields(shell.UnifiedAdmissionRuleEvaluation)
    ) == shell.RESULT_FIELDS
    assert dataclasses.is_dataclass(shell.UnifiedAdmissionDispatchError)
    assert shell.UnifiedAdmissionDispatchError.__dataclass_params__.frozen is True
    assert tuple(
        field.name for field in dataclasses.fields(shell.UnifiedAdmissionDispatchError)
    ) == shell.DISPATCH_ERROR_FIELDS
    error = shell.UnifiedAdmissionDispatchError(
        "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
        "ADMIT_999",
        False,
        False,
        False,
        "unknown rule",
    )
    assert str(error) == "unknown rule"
    assert error.args == ("unknown rule",)
    assert isinstance(shell.EVALUATOR_REGISTRY, MappingProxyType)
    assert tuple(shell.EVALUATOR_REGISTRY) == ("ADMIT_004",)
    signature = inspect.signature(shell.evaluate_admission_rule)
    assert tuple(signature.parameters) == (
        "admission_rule_id",
        "candidate_record",
        "batch_context",
        "evaluation_context",
        "download_result_context",
        "stage_authorization_context",
    )
    assert signature.parameters["batch_context"].kind is inspect.Parameter.KEYWORD_ONLY
    assert signature.parameters["stage_authorization_context"].default is None

    candidate = shell._base_candidate(residue="cys")
    context = shell._base_context(candidate)
    result = shell.evaluate_admission_rule(
        "ADMIT_004", candidate, evaluation_context=context
    )
    assert result == shell.UnifiedAdmissionRuleEvaluation(
        shell.RESULT_SCHEMA_VERSION,
        "ADMIT_004",
        shell.ADMIT_004_RULE_NAME,
        "passed",
        True,
        False,
        "",
        (("covalent_residue_name", "CYS"),),
        result.validated_candidate_fields,
        shell.ADMIT_004_CANDIDATE_FIELDS,
        ("covalent_residue_identity_evidence_context",),
        False,
        shell.ADMIT_004_ADAPTER_ID,
    )
    dispatch_expectations = (
        ("ADMIT_001", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"),
        ("ADMIT_005", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"),
        ("ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN"),
    )
    for rule_id, code in dispatch_expectations:
        try:
            shell.evaluate_admission_rule(rule_id, candidate)
        except shell.UnifiedAdmissionDispatchError as dispatch_error:
            assert dispatch_error.code == code
        else:
            raise AssertionError(f"{rule_id} did not fail closed")

    truth_rows = state["truth_rows"]
    assert len(truth_rows) == 24
    assert len({row["case_id"] for row in truth_rows}) == 24
    assert Counter(row["truth_group"] for row in truth_rows) == Counter(
        {"passed": 3, "blocked": 4, "invalid_rule_result": 3, "dispatch_error": 14}
    )
    assert all(row["truth_passed"] == "true" for row in truth_rows)
    registry_rows = state["registry_rows"]
    assert len(registry_rows) == 15
    assert tuple(row["admission_rule_id"] for row in registry_rows) == shell.KNOWN_RULE_IDS
    assert tuple(row["registered"] for row in registry_rows).count("true") == 1
    assert registry_rows[3]["registered"] == "true"
    assert all(row["audit_passed"] == "true" for row in registry_rows)


def run_checks() -> dict[str, Any]:
    snapshot = shell.build_frozen_source_snapshot()
    assert shell.validate_frozen_source_snapshot(snapshot)
    assert len(snapshot.records) == 12
    assert tuple(record.relative_path for record in snapshot.records) == shell.SOURCE_PATHS
    assert all(
        record.expected_sha256
        == record.base_tree_sha256
        == record.filesystem_sha256
        == hashlib.sha256(record.content_bytes).hexdigest()
        for record in snapshot.records
    )
    predecessor = shell._validate_predecessors(snapshot)
    assert len(predecessor["issues"].rows) == 12
    assert len(predecessor["routing"].rows) == 15
    assert len(predecessor["admit_truth"].rows) == 50

    state = shell.build_phase2_state(snapshot)
    assert state["all_checks_passed"] is True
    _assert_runtime_contract(state)
    issue_map = {row["issue_id"]: row for row in state["issue_rows"]}
    assert len(issue_map) == 12
    assert issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["issue_count"] == "11"
    assert issue_map[
        "UNIFIED_ADMISSION_LEGACY_EVALUATOR_ADAPTER_SEMANTICS_UNRESOLVED"
    ]["status"] == "open"
    assert issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] == "open"
    assert issue_map[
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"
    ]["status"] == "open"

    expected_payloads, expected_manifest = _expected_materialization()
    materialized = shell.run_covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1()
    assert materialized["manifest"] == expected_manifest
    default_hashes = validate_output_root(
        materialized["output_root"], expected_payloads, expected_manifest
    )
    contract_rows = _csv_rows(expected_payloads[shell.CONTRACT_FILENAME], shell.CONTRACT_COLUMNS)
    truth_rows = _csv_rows(expected_payloads[shell.TRUTH_FILENAME], shell.TRUTH_COLUMNS)
    registry_rows = _csv_rows(expected_payloads[shell.REGISTRY_FILENAME], shell.REGISTRY_COLUMNS)
    safety_rows = _csv_rows(expected_payloads[shell.SAFETY_FILENAME], shell.SAFETY_COLUMNS)
    issue_rows = _csv_rows(expected_payloads[shell.ISSUE_FILENAME], shell.ISSUE_COLUMNS)
    assert len(contract_rows) == 31 and all(row["contract_passed"] == "true" for row in contract_rows)
    assert len(truth_rows) == 24 and all(row["truth_passed"] == "true" for row in truth_rows)
    assert len(registry_rows) == 15 and all(row["audit_passed"] == "true" for row in registry_rows)
    assert len(safety_rows) == len(shell.TRUE_SAFETY_ITEMS) + len(shell.FALSE_SAFETY_ITEMS)
    assert all(row["safety_passed"] == "true" for row in safety_rows)
    assert issue_rows == predecessor["issues"].rows

    _assert_materializer_safety(expected_payloads, expected_manifest)
    _assert_output_failure_modes(expected_payloads, expected_manifest)
    assert not tuple(materialized["output_root"].glob("*.tmp"))
    assert not tuple(materialized["output_root"].glob("*.part"))
    assert len(default_hashes) == 6
    return {
        "all_checks_passed": True,
        "exact_source_count": 12,
        "truth_matrix_pass_count": 24,
        "truth_matrix_group_counts": dict(state["truth_group_counts"]),
        "registry_audit_pass_count": 15,
        "active_issue_count": 12,
        "provider_blocking_issue_count": 11,
        "registered_rule_ids": ["ADMIT_004"],
        "output_file_count": 6,
        "output_sha256": default_hashes,
        "deterministic_double_materialization": True,
        "materializer_symlink_victim_fail_closed": True,
        "output_failure_modes_fail_closed": True,
        "ready_for_bulk_download_now": False,
        "ready_for_training": False,
    }


if __name__ == "__main__":
    report = run_checks()
    assert report["all_checks_passed"] is True
    assert report["exact_source_count"] == 12
    assert report["truth_matrix_pass_count"] == 24
    assert report["registry_audit_pass_count"] == 15
    assert report["active_issue_count"] == 12
    assert report["provider_blocking_issue_count"] == 11
    assert report["registered_rule_ids"] == ["ADMIT_004"]
    assert report["output_file_count"] == 6
    assert len(report["output_sha256"]) == 6
    assert report["deterministic_double_materialization"] is True
    assert report["materializer_symlink_victim_fail_closed"] is True
    assert report["output_failure_modes_fail_closed"] is True
    assert report["ready_for_bulk_download_now"] is False
    assert report["ready_for_training"] is False
    print(json.dumps(report, indent=2, sort_keys=True))
