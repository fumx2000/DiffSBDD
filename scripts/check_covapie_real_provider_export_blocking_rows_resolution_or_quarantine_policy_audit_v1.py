#!/usr/bin/env python3
"""Independently verify and optionally materialize the blocking-row audit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_real_provider_export_blocking_rows_resolution_or_quarantine_policy_audit_v1
    as gate,
)

EXACT10 = (
    Path("src/covalent_ext/covapie_real_provider_export_blocking_rows_resolution_or_quarantine_policy_audit_v1.py"),
    Path("tests/test_covapie_real_provider_export_blocking_rows_resolution_or_quarantine_policy_audit_v1.py"),
    Path("scripts/check_covapie_real_provider_export_blocking_rows_resolution_or_quarantine_policy_audit_v1.py"),
    Path("docs/covapie_real_provider_export_blocking_rows_resolution_or_quarantine_policy_audit_v1_summary.md"),
    *(gate.OUTPUT_ROOT / name for name in gate.OUTPUT_FILES),
)


def _show(path: Path) -> bytes:
    spec = f"{gate.BASE_COMMIT}:{path.as_posix()}"
    subprocess.run(
        ("git", "cat-file", "-e", spec), cwd=ROOT, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return subprocess.run(
        ("git", "show", spec), cwd=ROOT, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"), newline="")))


def _state_code(state: str, code: str) -> tuple[str, str]:
    if state not in ("absent", "present", "unknown"):
        return "invalid", "unsupported_state"
    if state == "present":
        return (
            ("valid", "explicit_present") if code
            else ("invalid", "present_requires_nonempty")
        )
    if code:
        return "invalid", f"{state}_requires_empty"
    if state == "unknown":
        return "blocked", gate.UNKNOWN_REASON
    return "valid", "explicit_absent"


def _classifier(**overrides):
    values = {
        "state_field_present": True,
        "code_field_present": True,
        "state": "absent",
        "code": "",
        "provider_provenance_complete": True,
        "residue_identity_unique": True,
        "auth_label_consistent": True,
        "raw_required": False,
        "heuristic_required": False,
        "admit_outcome": "blocked",
        "admit_reason": "BLOCKED",
        "recorded_provider_status": "exported_blocking",
        "recorded_blocking_reason": "BLOCKED",
    }
    values.update(overrides)
    return gate.classify_covapie_real_provider_export_blocking_row_evidence_v1(
        **values
    )


def _independent_evidence_check() -> tuple[list[dict[str, str]], dict[str, object]]:
    predecessor = json.loads(_show(gate.PREDECESSOR_MANIFEST))
    assert predecessor["effective_open_issues"] == [gate.ISSUE_ID]
    assert predecessor["atom_pair_issue_resolved"] is True
    assert predecessor["ready_for_tensorization"] is False
    issue_payload = _show(gate.PREDECESSOR_ISSUES)
    assert hashlib.sha256(issue_payload).hexdigest() == (
        "09ee8271157343c4fd39c2edd73e38d6f0e896b8da247d8e3a8588c0b1cd0afa"
    )
    issue_map = {row["issue_id"]: row for row in _rows(issue_payload)}
    provider = issue_map[gate.ISSUE_ID]
    assert provider["affected_fields"] == (
        "covalent_residue_insertion_code_state|"
        "covalent_residue_insertion_code"
    )
    assert provider["affected_rules"] == "ADMIT_004"
    assert provider["status"] == "open"
    assert provider["issue_count"] == "11"
    assert provider["issue_origin"] == gate.ISSUE_ORIGIN

    sidecar_payload = _show(gate.ORIGIN_SIDECAR)
    sidecar = [
        row for row in _rows(sidecar_payload)
        if row["provider_export_status"] == "exported_blocking"
    ]
    bindings = {
        row["binding_row_id"]: row for row in _rows(_show(gate.BINDING_MATRIX))
    }
    overlay = {
        row["binding_row_id"]: row
        for row in _rows(_show(gate.INTEGRATION_OVERLAY))
    }
    downstream = {
        row["binding_row_id"]: row
        for row in _rows(_show(gate.INTEGRATION_EVIDENCE))
    }
    assert len(sidecar) == len({row["binding_row_id"] for row in sidecar}) == 11
    for order, row in enumerate(sidecar, start=1):
        identity = row["binding_row_id"]
        assert identity == f"REAL_LOCATOR_BINDING_{order:06d}"
        binding = bindings[identity]
        assert binding["covalent_residue_name"] == "CYS"
        assert binding["selected_residue_atom_name"] == "SG"
        assert _state_code(
            row["covalent_residue_insertion_code_state"],
            row["covalent_residue_insertion_code"],
        ) == ("blocked", gate.UNKNOWN_REASON)
        assert row["provider_export_blocking_reason"] == gate.UNKNOWN_REASON
        for field in (
            "covalent_residue_locator_namespace",
            "covalent_residue_insertion_code_state",
            "covalent_residue_insertion_code",
            "covalent_residue_locator_provenance_source_id",
            "covalent_residue_locator_provenance_sha256",
        ):
            assert overlay[identity][field] == row[field]
        assert downstream[identity]["integration_status"] == "integrated_blocking"
        assert downstream[identity]["integration_blocking_reason"] == gate.UNKNOWN_REASON

    admit_source = _show(gate.ADMIT_SOURCE).decode("utf-8")
    for token in (
        'state not in ("absent", "present", "unknown")',
        'if state == "absent":',
        'if state == "unknown":',
        'if state == "unknown" and value == "":',
    ):
        assert token in admit_source
    assert len(_rows(_show(gate.ADMIT_TRUTH))) == 50
    assert len(_rows(_show(gate.DISPATCH_ROUTING))) == 15
    assert _classifier(
        state_field_present=False, state="", code=""
    )[0] == gate.DISPOSITIONS[1]
    assert _classifier(
        code_field_present=False, state="absent", code=None
    )[0] == gate.DISPOSITIONS[1]
    assert _classifier(
        state_field_present=True, state="unsupported", code=""
    )[0] == gate.DISPOSITIONS[2]
    return sidecar, predecessor


def _verify_materialized(expected: dict[str, bytes]) -> dict[str, object]:
    for name, payload in expected.items():
        assert (ROOT / gate.OUTPUT_ROOT / name).read_bytes() == payload
    audit = _rows(expected[gate.BLOCKING_MATRIX_FILE])
    sufficiency = _rows(expected[gate.SUFFICIENCY_MATRIX_FILE])
    policy = _rows(expected[gate.POLICY_MATRIX_FILE])
    sources = _rows(expected[gate.SOURCE_INVENTORY_FILE])
    manifest = json.loads(expected[gate.MANIFEST_FILE])
    assert len(audit) == 11
    assert len(sufficiency) == 165
    assert len(policy) == 17
    assert len(sources) == len(gate.SOURCE_ROLES) == 28
    for source in sources:
        path = Path(source["source_path"])
        payload = _show(path)
        assert hashlib.sha256(payload).hexdigest() == source["source_sha256"]
        assert source["source_sha256"] == gate.FROZEN_SHA256[path]
        assert source["committed_in_base"] == "True"
        assert source["verified"] == "True"
    assert [row["case_id"] for row in policy] == [
        case_id for case_id, _ in gate.POLICY_CASES
    ]
    for row in policy:
        decision = (
            gate.evaluate_covapie_real_provider_export_resolution_or_quarantine_policy_case_v1(
                row["case_id"]
            )
        )
        assert row["expected_disposition"] == decision.disposition
        assert row["expected_reason"] == decision.reason
        assert row["resolution_allowed"] == str(decision.resolution_allowed)
        assert row["quarantine_allowed"] == str(decision.quarantine_allowed)
        assert row["contradiction_resolution_required"] == str(
            decision.contradiction_resolution_required
        )
        assert row["provider_row_mutation_allowed"] == str(
            decision.provider_row_mutation_allowed
        )
        assert row["fails_closed"] == str(decision.fails_closed)
        assert row["verified"] == "True"
        inputs = gate._policy_classifier_inputs(row["case_id"])
        if inputs is not None:
            classifier = (
                gate.classify_covapie_real_provider_export_blocking_row_evidence_v1(
                    **inputs
                )
            )
            assert classifier == (decision.disposition, decision.reason)
    assert all(row["verified"] == "True" for row in audit)
    assert all(
        row["audit_disposition"]
        == "quarantine_required_pending_provider_reexport"
        for row in audit
    )
    assert all(row["observed_insertion_code_state"] == "unknown" for row in audit)
    assert all(row["observed_insertion_code"] == "" for row in audit)
    assert all(row["admit_004_outcome"] == "blocked" for row in audit)
    assert all(row["admit_004_reason"] == gate.UNKNOWN_REASON for row in audit)
    assert expected[gate.ISSUE_INVENTORY_FILE] == _show(gate.PREDECESSOR_ISSUES)
    for name, digest in manifest["evidence_sha256"].items():
        assert hashlib.sha256(expected[name]).hexdigest() == digest
    assert manifest["provider_issue_resolved"] is False
    assert manifest["atom_pair_issue_resolved"] is True
    assert manifest["raw_read"] is False
    assert manifest["network_used"] is False
    assert manifest["provider_used"] is False
    assert manifest["ready_for_feature_semantics_audit"] is False
    assert manifest["ready_for_tensorization"] is False
    assert manifest["feature_semantics_audit_completed"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["policy_matrix_executable"] is True
    assert manifest["policy_matrix_classifier_consistency_verified"] is True
    assert manifest["missing_state_disposition"] == gate.DISPOSITIONS[1]
    assert manifest["missing_code_field_disposition"] == gate.DISPOSITIONS[1]
    assert manifest["unsupported_state_disposition"] == gate.DISPOSITIONS[2]
    return manifest


def _safety_check() -> None:
    status = subprocess.run(
        ("git", "status", "--short", "--untracked-files=all"),
        cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.decode().splitlines()
    allowed = {f"?? {path.as_posix()}" for path in EXACT10}
    assert set(status).issubset(allowed)
    assert len(EXACT10) == len(set(EXACT10)) == 10
    for path in EXACT10:
        target = ROOT / path
        assert not target.is_symlink()
        if target.exists():
            assert target.is_file()
            assert target.stat().st_size < 100 * 1024 * 1024
        assert path.parts[:2] != ("data", "raw")
        assert path.suffix not in {
            ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
            ".tgz", ".npz", ".tmp", ".part",
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--materialize", action="store_true")
    args = parser.parse_args()
    sidecar, _ = _independent_evidence_check()
    builds = [
        gate.build_covapie_real_provider_export_blocking_rows_policy_audit_artifacts_v1(
            ROOT
        )
        for _ in range(3)
    ]
    assert builds[0] == builds[1] == builds[2]
    expected = builds[0]
    if args.materialize:
        output_root = ROOT / gate.OUTPUT_ROOT
        output_root.mkdir(parents=True, exist_ok=True)
        existing = {path.name for path in output_root.iterdir()}
        if existing != set(gate.OUTPUT_FILES):
            raise ValueError("materialization target is not the exact output set")
        for name, payload in expected.items():
            (output_root / name).write_bytes(payload)
    manifest = _verify_materialized(expected)
    result = gate.derive_covapie_real_provider_export_blocking_rows_policy_audit_v1(
        ROOT
    )
    decision = result["decision"]
    assert gate.serialize_covapie_real_provider_export_blocking_rows_policy_audit_decision_v1(
        decision
    ) == gate.serialize_covapie_real_provider_export_blocking_rows_policy_audit_decision_v1(
        gate.derive_covapie_real_provider_export_blocking_rows_policy_audit_v1(
            ROOT
        )["decision"]
    )
    assert len(sidecar) == decision.blocking_row_count == 11
    _safety_check()
    report = {
        "audit_outcome": decision.outcome,
        "blocking_row_count": decision.blocking_row_count,
        "unique_blocking_row_count": decision.unique_blocking_row_count,
        "admit_004_contract_verified": decision.admit_004_contract_verified,
        "resolvable_from_committed_evidence_count": decision.resolvable_from_committed_evidence_count,
        "quarantine_required_count": decision.quarantine_required_count,
        "contradictory_or_invalid_count": decision.contradictory_or_invalid_count,
        "all_rows_classified": decision.all_rows_classified,
        "resolution_or_quarantine_policy_frozen": decision.resolution_or_quarantine_policy_frozen,
        "provider_rows_mutated": decision.provider_rows_mutated,
        "provider_issue_resolved": decision.provider_issue_resolved,
        "ready_for_resolution_materialization": decision.ready_for_resolution_materialization,
        "ready_for_quarantine_materialization": decision.ready_for_quarantine_materialization,
        "ready_for_feature_semantics_audit": decision.ready_for_feature_semantics_audit,
        "ready_for_tensorization": decision.ready_for_tensorization,
        "feature_semantics_audit_completed": manifest["feature_semantics_audit_completed"],
        "ready_for_training": decision.ready_for_training,
        "recommended_next_step": decision.recommended_next_step,
    }
    for key, value in report.items():
        if type(value) is bool:
            value = str(value).lower()
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
