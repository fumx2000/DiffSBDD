#!/usr/bin/env python3
"""Check Step14AU-E1-E4 Phase 4 runtime and output evidence directly."""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import inspect
import io
import json
import os
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
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004
    as runtime,
)


EXPECTED_OUTPUT_SHA256 = {
    runtime.CONTRACT_FILENAME: "be8cbe4db8a8b506bc4300b8c7d32a994c8088ac6aa2b34340e36dc9b9a83498",
    runtime.TRUTH_FILENAME: "5e47d644d3376d69951ff0746eeba2a89194f4c6a074d3c7136b2b19168f88a7",
    runtime.REGISTRY_FILENAME: "23b440c51d4cb4a924124d8bed9bbac21328c1fcab62aee115134901f49a3e1f",
    runtime.SAFETY_FILENAME: "70f4eeb010362eb9cf7ca727932056b52bd58dba6a18b12b4245bb55183ada64",
    runtime.ISSUE_FILENAME: "27bed0fd2250e0c64c704771fdb2bca8f5e50554d99f53694dc579f85f578d1f",
    runtime.MANIFEST_FILENAME: "9cf7e902566a4aef9aa098e9a9a966f925666df581f8c0ce408d8c9598905149",
}


def _csv_rows(content: bytes, columns: tuple[str, ...]) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(
        io.StringIO(content.decode("utf-8", errors="strict"), newline="")
    )
    if tuple(reader.fieldnames or ()) != columns:
        raise AssertionError("output CSV header mismatch")
    rows = tuple(dict(row) for row in reader)
    if any(
        tuple(row) != columns or any(value is None for value in row.values())
        for row in rows
    ):
        raise AssertionError("output CSV row mismatch")
    return rows


def _expected_materialization() -> tuple[dict[str, bytes], dict[str, Any]]:
    snapshot = runtime.build_frozen_source_snapshot()
    assert runtime.validate_frozen_source_snapshot(snapshot)
    assert len(snapshot.records) == 14
    state = runtime.build_phase4_state(snapshot)
    assert state["all_checks_passed"] is True
    payloads, manifest = runtime._payloads(state)
    assert tuple(payloads) == runtime.OUTPUT_FILES
    assert len(payloads) == 6
    return payloads, manifest


def validate_output_root(
    root: Path,
    expected_payloads: Mapping[str, bytes],
    expected_manifest: Mapping[str, Any],
) -> dict[str, str]:
    metadata = os.lstat(root)
    assert stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
    entries = tuple(root.iterdir())
    assert {entry.name for entry in entries} == set(runtime.OUTPUT_FILES)
    actual_bytes: dict[str, bytes] = {}
    actual_hashes: dict[str, str] = {}
    for name in runtime.OUTPUT_FILES:
        path = root / name
        entry_metadata = os.lstat(path)
        assert stat.S_ISREG(entry_metadata.st_mode)
        assert not stat.S_ISLNK(entry_metadata.st_mode)
        content = path.read_bytes()
        actual_bytes[name] = content
        actual_hashes[name] = hashlib.sha256(content).hexdigest()
        assert content == expected_payloads[name]
        assert actual_hashes[name] == EXPECTED_OUTPUT_SHA256[name]
    actual_manifest = json.loads(
        actual_bytes[runtime.MANIFEST_FILENAME].decode("utf-8", errors="strict")
    )
    assert type(actual_manifest) is dict
    assert actual_manifest == expected_manifest
    assert set(actual_manifest["output_sha256"]) == set(runtime.CSV_OUTPUTS)
    for name in runtime.CSV_OUTPUTS:
        assert actual_manifest["output_sha256"][name] == actual_hashes[name]
    truth_rows = _csv_rows(actual_bytes[runtime.TRUTH_FILENAME], runtime.TRUTH_COLUMNS)
    registry_rows = _csv_rows(
        actual_bytes[runtime.REGISTRY_FILENAME], runtime.REGISTRY_COLUMNS
    )
    issue_rows = _csv_rows(actual_bytes[runtime.ISSUE_FILENAME], runtime.ISSUE_COLUMNS)
    safety_rows = _csv_rows(
        actual_bytes[runtime.SAFETY_FILENAME], runtime.SAFETY_COLUMNS
    )
    assert len(truth_rows) == 56
    assert len({row["case_id"] for row in truth_rows}) == 56
    assert Counter(row["truth_group"] for row in truth_rows) == {
        "passed": 8,
        "blocked": 4,
        "invalid_rule_result": 24,
        "dispatch_error": 20,
    }
    assert all(row["truth_passed"] == "true" for row in truth_rows)
    assert len(registry_rows) == 15
    assert tuple(row["admission_rule_id"] for row in registry_rows) == runtime.KNOWN_RULE_IDS
    assert all(row["audit_passed"] == "true" for row in registry_rows)
    assert tuple(
        row["admission_rule_id"] for row in registry_rows if row["registered"] == "true"
    ) == ("ADMIT_001", "ADMIT_002", "ADMIT_003", "ADMIT_004")
    assert len(issue_rows) == 11
    assert runtime.REMOVED_ISSUE_ID not in {row["issue_id"] for row in issue_rows}
    issue_map = {row["issue_id"]: row for row in issue_rows}
    assert issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["status"] == "open"
    assert issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["severity"] == "blocking"
    assert issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["issue_count"] == "11"
    assert issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] == "open"
    assert (
        issue_map["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"][
            "status"
        ]
        == "open"
    )
    assert tuple(row["safety_item"] for row in safety_rows) == (
        *runtime.TRUE_SAFETY_ITEMS,
        *runtime.FALSE_SAFETY_ITEMS,
    )
    assert all(row["safety_passed"] == "true" for row in safety_rows)
    for item in runtime.TRUE_READINESS:
        assert actual_manifest["readiness"][item] is True
        assert actual_manifest[item] is True
    for item in runtime.FALSE_READINESS:
        assert actual_manifest["readiness"][item] is False
        assert actual_manifest[item] is False
    assert actual_manifest["unified_rule_engine_implemented"] is False
    assert actual_manifest["admit_005_to_015_registered_in_engine"] is False
    assert actual_manifest["evaluate_all_rules_implemented"] is False
    assert actual_manifest["combined_candidate_verdict_implemented"] is False
    assert actual_manifest["cross_rule_precedence_frozen"] is False
    assert actual_manifest["real_candidate_evaluation"] is False
    assert actual_manifest["exact11_real_rows_evaluated"] is False
    assert actual_manifest["ready_for_bulk_download_now"] is False
    assert actual_manifest["ready_for_training"] is False
    assert actual_manifest["ready_to_train_now"] is False
    assert not tuple(root.glob("*.tmp"))
    assert not tuple(root.glob("*.part"))
    return actual_hashes


def _assert_dispatch_error(
    rule_id: object,
    expected: tuple[str, str, bool, bool, bool],
    **contexts: object,
) -> runtime.UnifiedAdmissionDispatchError:
    try:
        runtime.evaluate_admission_rule(rule_id, {}, **contexts)  # type: ignore[arg-type]
    except runtime.UnifiedAdmissionDispatchError as error:
        observed = (
            error.code,
            error.admission_rule_id,
            error.known_rule,
            error.callable_discovered,
            error.adapter_ready,
        )
        assert observed == expected
        return error
    raise AssertionError("dispatch failure did not fail closed")


def _assert_runtime_contract() -> None:
    assert runtime.UnifiedAdmissionRuleEvaluation is runtime.phase2.UnifiedAdmissionRuleEvaluation
    assert runtime.UnifiedAdmissionDispatchError is runtime.phase2.UnifiedAdmissionDispatchError
    assert dataclasses.is_dataclass(runtime.UnifiedAdmissionRuleEvaluation)
    assert dataclasses.is_dataclass(runtime.UnifiedAdmissionDispatchError)
    assert tuple(
        field.name for field in dataclasses.fields(runtime.UnifiedAdmissionRuleEvaluation)
    ) == runtime.RESULT_FIELDS
    assert tuple(
        field.name for field in dataclasses.fields(runtime.UnifiedAdmissionDispatchError)
    ) == runtime.DISPATCH_ERROR_FIELDS
    assert str(inspect.signature(runtime.evaluate_admission_rule)) == (
        "(admission_rule_id: 'str', candidate_record: 'Mapping[str, object]', *, "
        "batch_context: 'Mapping[str, object] | None' = None, "
        "evaluation_context: 'Mapping[str, object] | None' = None, "
        "download_result_context: 'Mapping[str, object] | None' = None, "
        "stage_authorization_context: 'Mapping[str, object] | None' = None) -> "
        "'UnifiedAdmissionRuleEvaluation'"
    )
    assert type(runtime.EVALUATOR_REGISTRY) is MappingProxyType
    assert tuple(runtime.EVALUATOR_REGISTRY) == (
        "ADMIT_001",
        "ADMIT_002",
        "ADMIT_003",
        "ADMIT_004",
    )
    assert all(callable(handler) for handler in runtime.EVALUATOR_REGISTRY.values())
    assert runtime.ADAPTER_READY_RULE_IDS == tuple(runtime.EVALUATOR_REGISTRY)
    assert runtime.LEGACY_ADAPTER_NOT_READY_RULE_IDS == ()
    _assert_dispatch_error(
        1,
        ("UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "", False, False, False),
    )

    class RuleIdSubclass(str):
        pass

    _assert_dispatch_error(
        RuleIdSubclass("ADMIT_001"),
        ("UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "", False, False, False),
    )
    _assert_dispatch_error(
        "ADMIT_999",
        ("UNIFIED_ADMISSION_RULE_ID_UNKNOWN", "ADMIT_999", False, False, False),
    )
    _assert_dispatch_error(
        "ADMIT_005",
        ("UNIFIED_ADMISSION_RULE_NOT_REGISTERED", "ADMIT_005", True, False, False),
    )
    state = runtime.build_phase4_state()
    assert state["all_checks_passed"] is True
    assert len(state["truth_rows"]) == 56
    assert all(row["truth_passed"] == "true" for row in state["truth_rows"])
    assert len(state["registry_rows"]) == 15
    assert all(row["audit_passed"] == "true" for row in state["registry_rows"])


def _assert_legacy_oracle_calls_and_equivalence() -> None:
    specifications = (
        (
            runtime.admit001_legacy,
            "evaluate_admit_001_candidate_record_id",
            runtime.admit001_oracle,
            "evaluate_candidate_record_id_batch_uniqueness",
            "ADMIT_001",
            {"candidate_record_id": "REC_1"},
            {"batch_context": {"batch_candidate_record_ids": ["REC_1"]}},
        ),
        (
            runtime.admit002_legacy,
            "evaluate_admit_002_pdb_identifier",
            runtime.admit002_oracle,
            "normalize_pdb_identifier",
            "ADMIT_002",
            {"pdb_id": "1abc"},
            {},
        ),
        (
            runtime.admit003_legacy,
            "evaluate_admit_003_ligand_comp_id",
            runtime.admit003_oracle,
            "normalize_ligand_comp_id",
            "ADMIT_003",
            {"ligand_comp_id": "abc"},
            {},
        ),
    )
    for legacy_module, legacy_name, oracle_module, oracle_name, rule_id, candidate, kwargs in specifications:
        real_legacy = vars(legacy_module)[legacy_name]
        real_oracle = vars(oracle_module)[oracle_name]
        calls = {"legacy": 0, "oracle": 0}

        def counted_legacy(*args: object, _real=real_legacy) -> object:
            calls["legacy"] += 1
            return _real(*args)

        def counted_oracle(*args: object, _real=real_oracle) -> object:
            calls["oracle"] += 1
            return _real(*args)

        setattr(legacy_module, legacy_name, counted_legacy)
        setattr(oracle_module, oracle_name, counted_oracle)
        try:
            result = runtime.evaluate_admission_rule(rule_id, candidate, **kwargs)
            assert result.outcome == "passed"
            assert calls == {"legacy": 1, "oracle": 1}
        finally:
            setattr(legacy_module, legacy_name, real_legacy)
            setattr(oracle_module, oracle_name, real_oracle)

        def corrupt_legacy(*args: object, _real=real_legacy) -> dict[str, object]:
            source = _real(*args)
            source = dict(source)
            canonical_key = {
                "ADMIT_001": "normalized_candidate_record_id",
                "ADMIT_002": "canonical_pdb_id",
                "ADMIT_003": "canonical_ligand_comp_id",
            }[rule_id]
            source[canonical_key] = "KNOWN_WRONG_CANONICAL"
            return source

        setattr(legacy_module, legacy_name, corrupt_legacy)
        try:
            try:
                runtime.evaluate_admission_rule(rule_id, candidate, **kwargs)
            except runtime.UnifiedAdmissionDispatchError as error:
                assert error.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
                assert error.reason == f"{rule_id}_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
            else:
                raise AssertionError("semantic oracle mismatch returned a partial result")
        finally:
            setattr(legacy_module, legacy_name, real_legacy)


def _assert_admit004_preservation() -> None:
    candidate = runtime._admit004_candidate()
    context = runtime._admit004_context(candidate)
    direct = runtime.phase2.evaluate_admission_rule(
        "ADMIT_004", candidate, evaluation_context=context
    )
    successor = runtime.evaluate_admission_rule(
        "ADMIT_004", candidate, evaluation_context=context
    )
    assert successor == direct
    try:
        runtime.phase2.evaluate_admission_rule(
            "ADMIT_004", candidate, batch_context={}, evaluation_context=context
        )
    except runtime.UnifiedAdmissionDispatchError as direct_error:
        direct_fields = tuple(getattr(direct_error, name) for name in runtime.DISPATCH_ERROR_FIELDS)
    else:
        raise AssertionError("Phase 2 ADMIT_004 context error missing")
    try:
        runtime.evaluate_admission_rule(
            "ADMIT_004", candidate, batch_context={}, evaluation_context=context
        )
    except runtime.UnifiedAdmissionDispatchError as successor_error:
        successor_fields = tuple(
            getattr(successor_error, name) for name in runtime.DISPATCH_ERROR_FIELDS
        )
    else:
        raise AssertionError("successor ADMIT_004 context error missing")
    assert successor_fields == direct_fields
    real = runtime.phase2.evaluate_admission_rule
    calls = 0

    def counted(*args: object, **kwargs: object) -> runtime.UnifiedAdmissionRuleEvaluation:
        nonlocal calls
        calls += 1
        return direct

    runtime.phase2.evaluate_admission_rule = counted
    try:
        observed = runtime.evaluate_admission_rule(
            "ADMIT_004", candidate, evaluation_context=context
        )
        assert observed is direct
        assert calls == 1
    finally:
        runtime.phase2.evaluate_admission_rule = real


def _assert_materializer_and_output_failures(
    expected_payloads: Mapping[str, bytes], expected_manifest: Mapping[str, Any]
) -> None:
    with tempfile.TemporaryDirectory(prefix="covapie_phase4_checker_") as temporary:
        base = Path(temporary)
        first = base / "first"
        second = base / "second"
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1(first)
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1(second)
        first_hashes = validate_output_root(first, expected_payloads, expected_manifest)
        second_hashes = validate_output_root(second, expected_payloads, expected_manifest)
        assert first_hashes == second_hashes
        assert all(
            (first / name).read_bytes() == (second / name).read_bytes()
            for name in runtime.OUTPUT_FILES
        )
        victim = base / "victim"
        victim.write_bytes(b"victim-must-remain-unchanged")
        unsafe = base / "unsafe"
        unsafe.mkdir()
        (unsafe / runtime.CONTRACT_FILENAME).symlink_to(victim)
        try:
            runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1(unsafe)
        except ValueError:
            pass
        else:
            raise AssertionError("materializer symlink victim did not fail closed")
        assert victim.read_bytes() == b"victim-must-remain-unchanged"
        assert {entry.name for entry in unsafe.iterdir()} == {runtime.CONTRACT_FILENAME}

        def fresh(name: str) -> Path:
            root = base / name
            root.mkdir()
            for filename, content in expected_payloads.items():
                (root / filename).write_bytes(content)
            return root

        missing = fresh("missing")
        (missing / runtime.CONTRACT_FILENAME).unlink()
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

        tampered = fresh("tampered")
        (tampered / runtime.TRUTH_FILENAME).write_bytes(b"tampered\n")
        try:
            validate_output_root(tampered, expected_payloads, expected_manifest)
        except AssertionError:
            pass
        else:
            raise AssertionError("output tamper did not fail closed")

        overclaim = fresh("overclaim")
        manifest_path = overclaim / runtime.MANIFEST_FILENAME
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

        output_victim = base / "output-victim"
        output_victim.write_bytes(b"output-victim-must-remain-unchanged")
        symlinked = fresh("symlinked")
        link = symlinked / runtime.SAFETY_FILENAME
        link.unlink()
        link.symlink_to(output_victim)
        try:
            validate_output_root(symlinked, expected_payloads, expected_manifest)
        except AssertionError:
            pass
        else:
            raise AssertionError("symlink output did not fail closed")
        assert output_victim.read_bytes() == b"output-victim-must-remain-unchanged"
        assert not tuple(base.rglob("*.tmp"))
        assert not tuple(base.rglob("*.part"))


def main() -> int:
    expected_payloads, expected_manifest = _expected_materialization()
    _assert_runtime_contract()
    _assert_legacy_oracle_calls_and_equivalence()
    _assert_admit004_preservation()
    _assert_materializer_and_output_failures(expected_payloads, expected_manifest)
    output_hashes = validate_output_root(
        runtime.REPO_ROOT / runtime.DEFAULT_OUTPUT_ROOT,
        expected_payloads,
        expected_manifest,
    )
    assert expected_manifest["all_checks_passed"] is True
    assert expected_manifest["source_input_count"] == 14
    assert expected_manifest["truth_matrix_pass_count"] == 56
    assert expected_manifest["registry_audit_pass_count"] == 15
    assert expected_manifest["active_issue_count"] == 11
    assert expected_manifest["provider_blocking_issue_count"] == 11
    assert tuple(expected_manifest["registered_rule_ids"]) == (
        "ADMIT_001",
        "ADMIT_002",
        "ADMIT_003",
        "ADMIT_004",
    )
    assert output_hashes == EXPECTED_OUTPUT_SHA256
    print("all_checks_passed=true")
    print("source_input_count=14")
    print("phase2_type_identity_reused=true")
    print("registered_rule_ids=ADMIT_001|ADMIT_002|ADMIT_003|ADMIT_004")
    print("truth_matrix=56/56")
    print("registry_audit=15/15")
    print("active_issue_count=11")
    print("provider_blocking_issue_count=11")
    for name in runtime.OUTPUT_FILES:
        assert len(output_hashes[name]) == 64
        print(f"output_sha256[{name}]={output_hashes[name]}")
    print(f"recommended_next_step={runtime.RECOMMENDED_NEXT_STEP}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
