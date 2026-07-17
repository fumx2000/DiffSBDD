#!/usr/bin/env python3
"""Fail-closed direct checker for Step14AU-E1-E1 design outputs."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate as gate,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path, columns: Sequence[str]) -> list[dict[str, str]]:
    assert path.is_file() and not path.is_symlink()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert tuple(reader.fieldnames or ()) == tuple(columns)
        rows = [dict(row) for row in reader]
    assert all(tuple(row) == tuple(columns) and all(value is not None for value in row.values()) for row in rows)
    return rows


def _standard_library_only(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    allowed = {
        "__future__", "ast", "collections", "csv", "hashlib", "io", "json",
        "os", "re", "stat", "subprocess", "sys", "tempfile", "dataclasses",
        "pathlib", "typing", "covalent_ext",
    }
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots <= allowed


def _direct_design_checks(state: Mapping[str, Any]) -> None:
    historical = state["historical"]
    e1c_contract = {row["contract_id"]: row for row in historical["e1c_contract"]}
    rule_map = {row["admission_rule_id"]: row for row in historical["rules"]}
    field_map = {row["field_name"]: row for row in historical["fields"]}
    context_map = {row["context_item"]: row for row in historical["contexts"]}
    admit_004 = rule_map["ADMIT_004"]
    admit_005 = rule_map["ADMIT_005"]
    assert admit_004["candidate_field_dependencies"] == "|".join(gate.CANDIDATE_FIELDS)
    assert admit_004["implementation_disposition"] == "rule_logic_ready"
    assert admit_004["evaluation_context_dependencies"] == "covalent_residue_identity_contract"
    assert admit_005["admission_rule_name"] == "cys_sg_scope_only_v1"
    assert admit_005["candidate_field_dependencies"] == "covalent_residue_name|covalent_residue_atom_name"
    assert field_map["covalent_residue_atom_name"]["source_value_contract"] == "must be SG for v1 Cys scope"
    assert field_map["covalent_residue_atom_name"]["dependent_rules"] == "ADMIT_004|ADMIT_005"
    assert context_map["covalent_residue_identity_contract"]["required_by_rules"] == "ADMIT_004"
    assert e1c_contract["INSERTION_GRAMMAR_005"]["expected_value"] == gate.INSERTION_PRESENT_VALUE_PATTERN
    assert e1c_contract["INSERTION_GRAMMAR_005"]["observed_value"] == gate.INSERTION_PRESENT_VALUE_PATTERN
    assert gate._INSERTION_RE.fullmatch("A/B") is not None
    assert gate._validate_insertion_state_value("present", "A/B") == ""
    assert gate._INSERTION_RE.fullmatch("A\\B") is None
    assert gate._validate_insertion_state_value("present", "A\\B") == "COVALENT_RESIDUE_INSERTION_PRESENT_CHARACTER_GRAMMAR_INVALID"
    assert gate._INSERTION_RE.fullmatch("A=B") is None
    assert gate._validate_insertion_state_value("present", "A=B") == "COVALENT_RESIDUE_INSERTION_PRESENT_CHARACTER_GRAMMAR_INVALID"
    assert gate._validate_insertion_state_value("present", "A{B") == ""
    assert gate._validate_insertion_state_value("present", "A}B") == ""
    assert gate._validate_insertion_state_value("absent", "") == ""
    assert gate._validate_insertion_state_value("unknown", "") == ""

    for value in ("SG", "CA", "ca", "N1", "OXT", "C1'", "A.B", "+"):
        atom = gate.validate_generic_covalent_residue_atom_name(value)
        assert atom.valid is True and atom.canonical_value == value and atom.reason == ""
    assert gate.validate_generic_covalent_residue_atom_name("X" * 10000).valid is True
    for value, reason in (
        (1, "COVALENT_RESIDUE_ATOM_NAME_TYPE_INVALID"),
        ("", "COVALENT_RESIDUE_ATOM_NAME_EMPTY"),
        ("SÉ", "COVALENT_RESIDUE_ATOM_NAME_NON_ASCII"),
        ("S G", "COVALENT_RESIDUE_ATOM_NAME_WHITESPACE_FORBIDDEN"),
        (".", "COVALENT_RESIDUE_ATOM_NAME_MARKER_FORBIDDEN"),
    ):
        atom = gate.validate_generic_covalent_residue_atom_name(value)
        assert atom.valid is False and atom.canonical_value is None and atom.reason == reason

    scope_expectations = (
        ("CYS", "SG", "passed", "passed"), ("cys", "SG", "passed", "passed"),
        ("CYS", "CA", "passed", "rejected"), ("SER", "SG", "passed", "rejected"),
        ("SER", "CA", "passed", "rejected"), ("CYS", "ca", "passed", "rejected"),
        ("C-Y", "SG", "invalid", "invalid"), ("CYS", "?", "invalid", "invalid"),
    )
    for residue, atom, admit4, admit5 in scope_expectations:
        result = gate.classify_admit_004_admit_005_atom_scope_design(residue, atom)
        assert (result.admit_004_outcome, result.admit_005_outcome) == (admit4, admit5)
        assert result.admit_004_outcome != "rejected"

    candidate = gate._base_candidate(state="present", value="A")
    context = gate._base_context(candidate)
    assert gate.classify_admit_004_identity_evidence_context_design(candidate, context) == gate.EvidenceContextDesignResult("passed", "")
    assert tuple(context[gate.EVIDENCE_CONTEXT_KEY]["attested_candidate_fields"]) == gate.CANDIDATE_FIELDS
    assert set(context[gate.EVIDENCE_CONTEXT_KEY]) == set(gate.NESTED_CONTEXT_KEYS)
    mismatch = gate._base_context(candidate)
    mismatch[gate.EVIDENCE_CONTEXT_KEY]["attested_candidate_fields"][gate.CANDIDATE_FIELDS[-1]] = "1" * 64
    assert gate.classify_admit_004_identity_evidence_context_design(candidate, mismatch).outcome == "invalid"
    missing = gate.classify_admit_004_identity_evidence_context_design(gate._base_candidate(), {})
    assert missing == gate.EvidenceContextDesignResult("blocked", gate.MISSING_CONTEXT_REASON)
    assert gate.classify_admit_004_identity_evidence_context_design(candidate, []).outcome == "invalid"
    assert gate.classify_admit_004_identity_evidence_context_design(
        candidate, gate._base_context(candidate, four_way=False)
    ) == gate.EvidenceContextDesignResult("blocked", gate.FOUR_WAY_REASON)
    assert gate.classify_admit_004_identity_evidence_context_design(
        candidate, gate._base_context(candidate, quote=False)
    ) == gate.EvidenceContextDesignResult("blocked", gate.QUOTE_CLASS_REASON)
    absent = gate._base_candidate()
    assert gate.classify_admit_004_identity_evidence_context_design(
        absent, gate._base_context(absent, four_way=False, quote=False)
    ).outcome == "passed"
    unknown = gate._base_candidate(state="unknown", value="")
    assert gate.classify_admit_004_identity_evidence_context_design(
        unknown, gate._base_context(unknown, outcome="blocked", reason="LATER_BLOCKER")
    ) == gate.EvidenceContextDesignResult("blocked", gate.UNKNOWN_REASON)


def check(output_root: Path = gate.DEFAULT_OUTPUT_ROOT) -> dict[str, Any]:
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    assert root.is_dir() and not root.is_symlink()
    assert {path.name for path in root.iterdir()} == set(gate.OUTPUT_FILES)
    assert all(path.is_file() and not path.is_symlink() for path in root.iterdir())
    assert not any(path.name.endswith((".tmp", ".part")) for path in root.iterdir())

    snapshot = gate.build_frozen_source_snapshot(REPO_ROOT)
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert all(
        record.expected_sha256 == record.base_tree_sha256 == record.filesystem_sha256
        == gate.SOURCE_SHA256[record.relative_path]
        for record in snapshot.records
    )
    state = gate.build_design_state(snapshot)
    assert state["source_ok"] is state["historical_evidence_ok"] is True
    assert state["design_readiness"] is state["all_checks_passed"] is True
    assert state["validation_failures"] == []
    assert state["contract_pass_count"] == 28 and state["truth_pass_count"] == 36
    _direct_design_checks(state)

    output_specs = (
        (gate.CONTRACT_FILENAME, gate.CONTRACT_COLUMNS, state["contract_rows"]),
        (gate.TRUTH_FILENAME, gate.TRUTH_COLUMNS, state["truth_rows"]),
        (gate.SOURCE_AUDIT_FILENAME, gate.SOURCE_AUDIT_COLUMNS, state["source_audit_rows"]),
        (gate.SAFETY_FILENAME, gate.SAFETY_COLUMNS, state["safety_rows"]),
        (gate.ISSUE_FILENAME, gate.ISSUE_COLUMNS, state["issue_rows"]),
    )
    for filename, columns, expected in output_specs:
        assert _csv(root / filename, columns) == list(expected)
    contract = _csv(root / gate.CONTRACT_FILENAME, gate.CONTRACT_COLUMNS)
    assert len(contract) == 28 and all(row["contract_passed"] == "true" for row in contract)
    contract_map = {row["contract_id"]: row for row in contract}
    assert contract_map["INSERTION_REUSE_001"] == {
        "contract_id": "INSERTION_REUSE_001",
        "contract_area": "insertion_reuse",
        "contract_statement": "E1-C insertion present-value grammar reused exactly without character-set drift",
        "expected_value": gate.INSERTION_PRESENT_VALUE_PATTERN,
        "observed_value": gate.INSERTION_PRESENT_VALUE_PATTERN,
        "contract_passed": "true",
    }
    truth = _csv(root / gate.TRUTH_FILENAME, gate.TRUTH_COLUMNS)
    assert len(truth) == 36 and all(row["truth_passed"] == "true" for row in truth)
    assert [sum(row["row_kind"] == kind for row in truth) for kind in (
        "generic_atom_valid", "generic_atom_invalid", "admit_004_admit_005_scope",
        "evidence_context_binding",
    )] == [8, 8, 8, 12]
    source_audit = _csv(root / gate.SOURCE_AUDIT_FILENAME, gate.SOURCE_AUDIT_COLUMNS)
    assert len(source_audit) == 16
    assert all(
        row["source_order"] == str(index)
        and row["source_relative_path"] == gate.SOURCE_PATHS[index - 1].as_posix()
        and row["sha256_expected"] == row["sha256_base_tree"] == row["sha256_filesystem"]
        == gate.SOURCE_SHA256[gate.SOURCE_PATHS[index - 1]]
        and row["source_verified"] == "true"
        for index, row in enumerate(source_audit, 1)
    )
    issues = _csv(root / gate.ISSUE_FILENAME, gate.ISSUE_COLUMNS)
    assert len(issues) == 10 and issues[:9] == list(state["historical"]["issues"])
    issue_map = {row["issue_id"]: row for row in issues}
    assert issue_map[gate.NEW_ISSUE] == {
        "issue_id": gate.NEW_ISSUE, "issue_type": "implementation_semantics_gap",
        "affected_fields": "covalent_residue_atom_name", "affected_rules": "ADMIT_004|ADMIT_005",
        "severity": "blocking", "status": "open", "blocking_scope": "admission_evaluator_rule_logic",
        "blocking_reason": gate.NEW_ISSUE, "issue_origin": "step14au_e1_e1_phase0_audit",
        "integration_transition": "design_frozen_pending_successor_integration", "issue_count": "1",
    }
    assert issue_map[gate.PROVIDER_ISSUE]["status"] == "open"
    assert issue_map[gate.PROVIDER_ISSUE]["issue_count"] == "11"

    csv_hashes = {filename: _sha256(root / filename) for filename in gate.CSV_OUTPUTS}
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert type(manifest) is dict and manifest == gate._manifest_payload(state, csv_hashes)
    assert not any(key in manifest for key in ("timestamp", "hostname", "host", "manifest_sha256"))
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]
    assert manifest["source_input_paths"] == [path.as_posix() for path in gate.SOURCE_PATHS]
    assert manifest["historical_e1d_admit_004_rule_logic_ready_claim"] is True
    assert manifest["generic_atom_scope_separation_conflict_detected"] is True
    assert manifest["contract_count"] == manifest["contract_pass_count"] == 28
    assert manifest["e1c_insertion_present_value_grammar_reused_exactly"] is True
    true_keys = (
        "generic_atom_identity_semantics_design_frozen",
        "admit_004_admit_005_scope_separation_design_frozen",
        "identity_evidence_context_schema_design_frozen",
        "candidate_attestation_binding_design_frozen",
        "ready_for_generic_atom_evidence_context_successor_integration",
        "feature_semantics_audit_required_before_training", "all_checks_passed",
    )
    false_keys = (
        "generic_atom_identity_semantics_integrated_into_effective_schema",
        "identity_evidence_context_integrated_into_effective_schema",
        "reconciled_admit_004_interface_implementation_ready", "admit_004_evaluator_implemented",
        "parser_quote_class_roundtrip_verified", "real_provider_present_value_roundtrip_ready",
        "real_provider_export_blocking_rows_resolved", "candidate_records_materialized",
        "ready_for_real_candidate_evaluation", "ready_for_bulk_download_now",
        "ready_for_training", "ready_to_train_now",
    )
    assert all(manifest[key] is True for key in true_keys)
    assert all(manifest[key] is False for key in false_keys)
    assert manifest["provider_blocking_issue_count"] == 11
    assert manifest["exact11_count"] == manifest["exact11_effective_blocked_count"] == 11
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    assert _csv(root / gate.SAFETY_FILENAME, gate.SAFETY_COLUMNS) == gate._safety_rows()

    production = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate.py"
    assert _standard_library_only(production) and _standard_library_only(Path(__file__))
    with tempfile.TemporaryDirectory(prefix="covapie_e1e1_a_") as first_name, tempfile.TemporaryDirectory(prefix="covapie_e1e1_b_") as second_name:
        first, second = Path(first_name), Path(second_name)
        gate.run_covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate_v1(first)
        gate.run_covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate_v1(second)
        assert all(
            (first / filename).read_bytes() == (second / filename).read_bytes() == (root / filename).read_bytes()
            for filename in gate.OUTPUT_FILES
        )
        assert not any(path.name.endswith((".tmp", ".part")) for directory in (first, second) for path in directory.iterdir())

    return {
        "source_count": 16,
        "historical_conflict_detected": True,
        "contract_passed": "28/28",
        "truth_passed": "36/36",
        "issue_count": 10,
        "provider_blocking_count": 11,
        "exact11_blocked": "11/11",
        "successor_integration_ready": True,
        "reconciled_interface_ready": False,
        "bulk_download_ready": False,
        "training_ready": False,
        "output_sha256": {filename: _sha256(root / filename) for filename in gate.OUTPUT_FILES},
    }


def main() -> int:
    result = check()
    assert result["source_count"] == 16
    assert result["historical_conflict_detected"] is True
    assert result["contract_passed"] == "28/28"
    assert result["truth_passed"] == "36/36"
    assert result["issue_count"] == 10
    assert result["provider_blocking_count"] == 11
    assert result["exact11_blocked"] == "11/11"
    assert result["successor_integration_ready"] is True
    assert result["reconciled_interface_ready"] is False
    assert result["bulk_download_ready"] is False
    assert result["training_ready"] is False
    assert len(result["output_sha256"]) == 6
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
