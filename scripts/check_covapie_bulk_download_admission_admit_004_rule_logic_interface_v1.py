#!/usr/bin/env python3
"""Direct checker for the standalone ADMIT_004 rule-logic interface v1."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import stat
import sys
import tempfile
from dataclasses import fields
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_004_rule_logic_interface as interface,
)


EXPECTED_RESULT_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_residue_name",
    "validated_candidate_fields",
    "consumed_candidate_fields",
    "evidence_context_consumed",
    "evaluator_io_used",
)


def _regular_output_files(root: Path) -> dict[str, bytes]:
    metadata = os.lstat(root)
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("output root is not a real directory")
    entries = tuple(root.iterdir())
    if {entry.name for entry in entries} != set(interface.OUTPUT_FILES):
        raise ValueError("output exact-set mismatch")
    result: dict[str, bytes] = {}
    for entry in entries:
        entry_metadata = os.lstat(entry)
        if stat.S_ISLNK(entry_metadata.st_mode) or not stat.S_ISREG(entry_metadata.st_mode):
            raise ValueError("unsafe output entry")
        result[entry.name] = entry.read_bytes()
    return result


def validate_output_root(root: Path, expected_payloads: dict[str, bytes]) -> dict[str, str]:
    actual = _regular_output_files(root)
    if actual != expected_payloads:
        raise ValueError("output bytes differ from direct deterministic reconstruction")
    manifest = json.loads(actual[interface.MANIFEST_FILENAME].decode("utf-8", errors="strict"))
    if type(manifest) is not dict:
        raise ValueError("manifest root invalid")
    if manifest.get("output_files") != list(interface.OUTPUT_FILES):
        raise ValueError("manifest output set invalid")
    if manifest.get("output_file_count") != 6:
        raise ValueError("manifest output count invalid")
    csv_hashes = {
        name: hashlib.sha256(actual[name]).hexdigest() for name in interface.CSV_OUTPUTS
    }
    if manifest.get("output_sha256") != csv_hashes:
        raise ValueError("manifest output SHA256 evidence invalid")
    if manifest.get("all_checks_passed") is not True:
        raise ValueError("manifest all-checks readiness invalid")
    if manifest.get("ready_for_admit_004_unified_rule_engine_integration") is not True:
        raise ValueError("manifest interface readiness invalid")
    forbidden_true = (
        "unified_rule_engine_integrated",
        "parser_quote_class_roundtrip_verified",
        "real_provider_present_value_roundtrip_ready",
        "real_provider_export_blocking_rows_resolved",
        "candidate_records_materialized",
        "exact11_real_rows_evaluated",
        "ready_for_real_candidate_evaluation",
        "ready_for_bulk_download_now",
        "ready_for_training",
        "ready_to_train_now",
    )
    if any(manifest.get(key) is not False for key in forbidden_true):
        raise ValueError("manifest readiness overclaim")
    for name in interface.CSV_OUTPUTS:
        reader = csv.DictReader(io.StringIO(actual[name].decode("utf-8"), newline=""))
        rows = list(reader)
        if reader.fieldnames is None or any(None in row.values() for row in rows):
            raise ValueError("output CSV invalid")
    return {
        name: hashlib.sha256(content).hexdigest()
        for name, content in sorted(actual.items())
    }


def _assert_core_evaluator() -> None:
    absent = interface._base_candidate()
    passed = interface.evaluate_admit_004(absent, interface._base_context(absent))
    assert passed.outcome == "passed" and passed.passed is True
    assert passed.blocks_candidate is False and passed.reason == ""
    assert passed.consumed_candidate_fields == interface.CANDIDATE_FIELDS
    assert len(passed.validated_candidate_fields) == 9
    assert passed.evaluator_io_used is False

    generic = interface._base_candidate(residue="SER", atom="CA")
    assert interface.evaluate_admit_004(generic, interface._base_context(generic)).outcome == "passed"
    unknown = interface._base_candidate(state="unknown", value="")
    unknown_result = interface.evaluate_admit_004(
        unknown,
        interface._base_context(unknown, outcome="blocked", reason="PROVIDER_BLOCKED"),
    )
    assert unknown_result.outcome == "blocked" and unknown_result.reason == interface.UNKNOWN_REASON
    malformed = interface._base_context(unknown)
    malformed[interface.EVIDENCE_CONTEXT_KEY]["schema_version"] = "wrong"  # type: ignore[index]
    malformed_result = interface.evaluate_admit_004(unknown, malformed)
    assert malformed_result.outcome == "invalid"
    assert malformed_result.reason == "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_SCHEMA_INVALID"
    provider_invalid = interface.evaluate_admit_004(
        unknown,
        interface._base_context(unknown, outcome="invalid", reason="PROVIDER_INVALID"),
    )
    assert provider_invalid.outcome == "invalid" and provider_invalid.reason == "PROVIDER_INVALID"

    lower = interface._base_candidate(residue="cys")
    lower_result = interface.evaluate_admit_004(lower, interface._base_context(lower))
    assert lower_result.canonical_residue_name == "CYS"
    mismatch = interface._base_context(lower)
    mismatch[interface.EVIDENCE_CONTEXT_KEY]["attested_candidate_fields"][
        "covalent_residue_name"
    ] = "CYS"  # type: ignore[index]
    mismatch_result = interface.evaluate_admit_004(lower, mismatch)
    assert mismatch_result.outcome == "invalid"
    assert mismatch_result.reason.endswith(":covalent_residue_name")


def run_check() -> dict[str, Any]:
    snapshot = interface.build_frozen_source_snapshot()
    assert interface.validate_frozen_source_snapshot(snapshot)
    assert tuple(record.relative_path for record in snapshot.records) == interface.SOURCE_PATHS
    assert all(
        record.expected_sha256 == record.base_tree_sha256 == record.filesystem_sha256
        for record in snapshot.records
    )
    predecessor = interface._validate_predecessor_evidence(snapshot)
    assert len(predecessor["issues"]) == 9
    assert predecessor["e1e2_manifest"]["exact11_count"] == 11
    assert predecessor["e1e2_manifest"]["exact11_effective_blocked_count"] == 11
    assert predecessor["e1e2_manifest"]["exact11_reason"] == interface.UNKNOWN_REASON

    _assert_core_evaluator()
    assert interface.Admit004EvaluationResult.__dataclass_params__.frozen is True
    assert tuple(field.name for field in fields(interface.Admit004EvaluationResult)) == EXPECTED_RESULT_FIELDS

    state = interface.build_interface_state(snapshot)
    assert state["all_checks_passed"] is True
    assert state["interface_implementation_readiness"] is True
    assert state["contract_pass_count"] == 43
    assert state["truth_pass_count"] == 50
    truth = state["truth_rows"]
    assert len(truth) == 50 and len({row["case_id"] for row in truth}) == 50
    assert all(row["truth_passed"] == "true" for row in truth)
    groups = {
        group: sum(row["truth_group"] == group for row in truth)
        for group in ("passed", "blocked", "candidate_invalid", "context_invalid")
    }
    assert groups == {
        "passed": 6,
        "blocked": 7,
        "candidate_invalid": 19,
        "context_invalid": 18,
    }
    assert state["issue_rows"] == list(predecessor["issues"])
    provider = next(row for row in state["issue_rows"] if row["issue_id"] == interface.PROVIDER_ISSUE)
    assert provider["status"] == "open"
    assert provider["severity"] == "blocking"
    assert provider["issue_count"] == "11"

    expected_payloads, expected_manifest = interface._payloads(state)
    assert expected_manifest["ready_for_admit_004_unified_rule_engine_integration"] is True
    assert expected_manifest["unified_rule_engine_integrated"] is False
    assert expected_manifest["exact11_real_rows_evaluated"] is False
    default_root = interface.REPO_ROOT / interface.DEFAULT_OUTPUT_ROOT
    output_hashes = validate_output_root(default_root, expected_payloads)

    with tempfile.TemporaryDirectory(prefix="covapie_admit_004_checker_") as directory:
        temporary_root = Path(directory)
        first = temporary_root / "first"
        second = temporary_root / "second"
        interface.run_covapie_bulk_download_admission_admit_004_rule_logic_interface_v1(first)
        interface.run_covapie_bulk_download_admission_admit_004_rule_logic_interface_v1(second)
        first_payloads = _regular_output_files(first)
        second_payloads = _regular_output_files(second)
        assert first_payloads == second_payloads == expected_payloads

        missing_root = temporary_root / "missing"
        interface.run_covapie_bulk_download_admission_admit_004_rule_logic_interface_v1(missing_root)
        (missing_root / interface.CONTRACT_FILENAME).unlink()
        try:
            validate_output_root(missing_root, expected_payloads)
        except ValueError:
            pass
        else:
            raise AssertionError("missing output did not fail closed")

        extra_root = temporary_root / "extra"
        interface.run_covapie_bulk_download_admission_admit_004_rule_logic_interface_v1(extra_root)
        (extra_root / "extra.txt").write_text("unsafe", encoding="utf-8")
        try:
            validate_output_root(extra_root, expected_payloads)
        except ValueError:
            pass
        else:
            raise AssertionError("extra output did not fail closed")

        tampered_root = temporary_root / "tampered"
        interface.run_covapie_bulk_download_admission_admit_004_rule_logic_interface_v1(tampered_root)
        (tampered_root / interface.TRUTH_FILENAME).write_bytes(b"tampered\n")
        try:
            validate_output_root(tampered_root, expected_payloads)
        except ValueError:
            pass
        else:
            raise AssertionError("hash drift did not fail closed")

        overclaim_root = temporary_root / "overclaim"
        interface.run_covapie_bulk_download_admission_admit_004_rule_logic_interface_v1(overclaim_root)
        overclaim_path = overclaim_root / interface.MANIFEST_FILENAME
        overclaim = json.loads(overclaim_path.read_text(encoding="utf-8"))
        overclaim["unified_rule_engine_integrated"] = True
        overclaim_path.write_text(json.dumps(overclaim, sort_keys=True), encoding="utf-8")
        try:
            validate_output_root(overclaim_root, expected_payloads)
        except ValueError:
            pass
        else:
            raise AssertionError("manifest overclaim did not fail closed")

        victim = temporary_root / "victim.txt"
        victim.write_text("unchanged", encoding="utf-8")
        symlink_root = temporary_root / "symlink"
        symlink_root.mkdir()
        (symlink_root / interface.CONTRACT_FILENAME).symlink_to(victim)
        try:
            interface.run_covapie_bulk_download_admission_admit_004_rule_logic_interface_v1(
                symlink_root
            )
        except ValueError:
            pass
        else:
            raise AssertionError("symlink output did not fail closed")
        assert victim.read_text(encoding="utf-8") == "unchanged"
        assert not any(
            path.name.endswith((".tmp", ".part"))
            for root in (first, second, symlink_root)
            for path in root.iterdir()
        )

    return {
        "exact_source_count": len(snapshot.records),
        "contract_pass_count": state["contract_pass_count"],
        "truth_pass_count": state["truth_pass_count"],
        "truth_group_counts": groups,
        "active_issue_count": len(state["issue_rows"]),
        "provider_blocking_issue_count": int(provider["issue_count"]),
        "exact11_metadata_count": predecessor["e1e2_manifest"]["exact11_count"],
        "output_sha256": output_hashes,
        "double_materialization_byte_identical": True,
        "symlink_victim_unchanged": True,
        "interface_ready_for_unified_engine_integration": True,
        "unified_rule_engine_integrated": False,
        "all_checks_passed": True,
    }


def main() -> None:
    report = run_check()
    assert report["exact_source_count"] == 12
    print(f"exact_source_count={report['exact_source_count']}")
    assert report["contract_pass_count"] == 43
    print(f"contract_pass_count={report['contract_pass_count']}")
    assert report["truth_pass_count"] == 50
    print(f"truth_pass_count={report['truth_pass_count']}")
    assert report["truth_group_counts"] == {
        "passed": 6,
        "blocked": 7,
        "candidate_invalid": 19,
        "context_invalid": 18,
    }
    print("truth_group_counts=" + json.dumps(report["truth_group_counts"], sort_keys=True))
    assert report["active_issue_count"] == 9
    print(f"active_issue_count={report['active_issue_count']}")
    assert report["provider_blocking_issue_count"] == 11
    print(f"provider_blocking_issue_count={report['provider_blocking_issue_count']}")
    assert report["exact11_metadata_count"] == 11
    print(f"exact11_metadata_count={report['exact11_metadata_count']}")
    assert len(report["output_sha256"]) == 6
    print("output_sha256=" + json.dumps(report["output_sha256"], sort_keys=True))
    assert report["double_materialization_byte_identical"] is True
    print("double_materialization_byte_identical=true")
    assert report["symlink_victim_unchanged"] is True
    print("symlink_victim_unchanged=true")
    assert report["interface_ready_for_unified_engine_integration"] is True
    print("interface_ready_for_unified_engine_integration=true")
    assert report["unified_rule_engine_integrated"] is False
    print("unified_rule_engine_integrated=false")
    assert report["all_checks_passed"] is True
    print("all_checks_passed=true")


if __name__ == "__main__":
    main()
