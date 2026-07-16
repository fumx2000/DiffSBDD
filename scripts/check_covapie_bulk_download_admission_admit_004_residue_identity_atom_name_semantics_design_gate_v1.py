#!/usr/bin/env python3
"""Fail-closed checker for CovaPIE Step14AU-E1-A."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate
    as gate,
)


EXPECTED_OUTPUT_SHA256 = {
    gate.CONTRACT_FILENAME: "a783a3d474a2ed4e5ff348ec54a73510f5f6f6fb9d1edcb45dc97108e5d09eff",
    gate.TRUTH_FILENAME: "a5c2d727b3178bd0e58643a1801780fa930cba2b89c14a058817ecb418753106",
    gate.EXACT11_FILENAME: "62f7c26b41daef96c32ca615b7d65a063810a53cef582a26cd54ed9cfb8b6e2a",
    gate.SAFETY_FILENAME: "02ae82b6db51dc6e4b96f8240af8852289012e33cc9620ef796ff5f5e8bb2711",
    gate.ISSUE_FILENAME: "fecb82397a853e900a53368dedc6bacf95fdc497fa6cd09c31a9be8a1e1d0577",
    gate.MANIFEST_FILENAME: "c442d31cebaea6b8e3ae5dbda232cc5ba377eb74a2ca68c2437ce0b43a39e6c0",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None and len(reader.fieldnames) == len(set(reader.fieldnames))
        rows = [dict(row) for row in reader]
    assert all(tuple(row) == tuple(reader.fieldnames) and all(value is not None for value in row.values()) for row in rows)
    return tuple(reader.fieldnames), rows


def _expected_rows(columns: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [{column: "true" if row[column] is True else "false" if row[column] is False else str(row[column])
             for column in columns} for row in rows]


def _validate_exact_output_set(root: Path) -> None:
    assert root.is_dir() and not root.is_symlink()
    assert {path.name for path in root.iterdir()} == set(gate.OUTPUT_FILES)
    assert all((root / name).is_file() and not (root / name).is_symlink() for name in gate.OUTPUT_FILES)
    assert not list(root.glob("*.tmp")) and not list(root.glob("*.part"))


def _validate_direct_source_bytes(state: Mapping[str, Any]) -> None:
    snapshot = state["source_snapshot"]
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert len(snapshot.records) == 22
    for record in snapshot.records:
        assert record.expected_sha256 == gate.SOURCE_SHA256[record.relative_path]
        assert record.observed_sha256 == record.expected_sha256
        assert hashlib.sha256(record.content_bytes).hexdigest() == record.expected_sha256


def _validate_result(result: Mapping[str, Any], root: Path) -> dict[str, str]:
    state, manifest = result["state"], result["manifest"]
    assert state["all_checks_passed"] is True and state["validation_failures"] == []
    assert state["source_ok"] is True and state["predecessors_ok"] is True
    assert gate.PROVENANCE_SOURCE_ID_PATTERN == r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$"
    assert gate.validate_provenance_identity("covapie:residue-locator:test", "0" * 64).valid
    assert gate.validate_provenance_identity("covapie/path:source", "0" * 64).valid
    assert gate.validate_provenance_identity("A" * 256, "0" * 64).valid
    assert not gate.validate_provenance_identity("A" * 257, "0" * 64).valid
    assert not gate.validate_provenance_identity("bad source", "0" * 64).valid
    cases = {row["case_id"]: row for row in gate._truth_case_specs()}
    case10, case11 = cases["ADMIT004_TRUTH_10"], cases["ADMIT004_TRUTH_11"]
    assert (case10["candidate_chain_id"], case10["candidate_residue_index"]) == ("A", "7")
    assert (case10["auth_chain_id"], case10["auth_residue_index"]) == ("A", "42")
    assert (case10["label_chain_id"], case10["label_residue_index"]) == ("L", "7")
    assert (case11["candidate_chain_id"], case11["candidate_residue_index"]) == ("B", "42")
    _validate_direct_source_bytes(state)
    assert len(state["truth_rows"]) == 16
    assert [row["case_id"] for row in state["truth_rows"]] == [f"ADMIT004_TRUTH_{value:02d}" for value in range(1, 17)]
    assert all(row["truth_table_passed"] is True for row in state["truth_rows"])
    assert len(state["exact11_rows"]) == 11 and all(row["audit_passed"] is True for row in state["exact11_rows"])
    assert sum(row["auth_label_conflict_observed"] is True for row in state["exact11_rows"]) == 3
    assert sum(row["auth_label_conflict_observed"] is False for row in state["exact11_rows"]) == 8
    assert all(row["canonical_residue_name"] == "CYS" for row in state["exact11_rows"])
    assert all(row["candidate_atom_name"] == row["matched_residue_atom_name"] == "SG" for row in state["exact11_rows"])
    assert all(row["locator_namespace"] == "auth" for row in state["exact11_rows"])
    assert all(row["admit_004_identity_semantics_valid"] is True for row in state["exact11_rows"])
    assert all(row["admit_005_scope_outcome"] == "passed" for row in state["exact11_rows"])
    assert all(row["insertion_state"] == "unknown" and row["insertion_value"] == "" for row in state["exact11_rows"])
    assert all(row["insertion_blocks"] is True and row["effective_outcome"] == "blocked" for row in state["exact11_rows"])
    assert all(row["reason"] == gate.UNKNOWN_REASON for row in state["exact11_rows"])
    target_issues = {"COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED", "COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED"}
    assert len(state["issue_rows"]) == 11
    assert all(row["status"] == "open" and row["severity"] == "blocking" for row in state["issue_rows"])
    assert all(row["integration_transition"] == "design_frozen_pending_successor_integration"
               for row in state["issue_rows"] if row["issue_id"] in target_issues)
    assert all(row["integration_transition"] == "unchanged_open"
               for row in state["issue_rows"] if row["issue_id"] not in target_issues)
    provider_issue = next(row for row in state["issue_rows"] if row["issue_id"] == "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT")
    assert provider_issue["issue_count"] == "11"
    assert all(row["contract_passed"] is True for row in state["contract_rows"])
    source_contract = [row for row in state["contract_rows"] if row["contract_area"] == "source_boundary" and row["contract_id"].startswith("SOURCE_") and row["contract_id"] != "SOURCE_COUNT"]
    assert len(source_contract) == 22
    assert [row["contract_id"] for row in source_contract] == [f"SOURCE_{value:03d}" for value in range(1, 23)]
    assert [row["contract_statement"].removeprefix("ordered committed regular non-symlink source ") for row in source_contract] == [path.as_posix() for path in gate.SOURCE_PATHS]
    assert [row["expected_value"] for row in source_contract] == [gate.SOURCE_SHA256[path] for path in gate.SOURCE_PATHS]
    assert all(row["observed_value"] == row["expected_value"] for row in source_contract)
    assert all(row["safety_passed"] is True for row in state["safety_rows"])

    _validate_exact_output_set(root)
    specs = (
        (gate.CONTRACT_FILENAME, gate.CONTRACT_COLUMNS, state["contract_rows"]),
        (gate.TRUTH_FILENAME, gate.TRUTH_COLUMNS, state["truth_rows"]),
        (gate.EXACT11_FILENAME, gate.EXACT11_COLUMNS, state["exact11_rows"]),
        (gate.SAFETY_FILENAME, gate.SAFETY_COLUMNS, state["safety_rows"]),
        (gate.ISSUE_FILENAME, gate.ISSUE_COLUMNS, state["issue_rows"]),
    )
    for filename, columns, rows in specs:
        header, disk_rows = _read_csv(root / filename)
        assert header == tuple(columns)
        assert disk_rows == _expected_rows(columns, rows)
    output_hashes = {name: _sha256(root / name) for name in gate.CSV_OUTPUTS}
    expected_manifest = gate._manifest_payload(state, output_hashes)
    disk_manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest == disk_manifest == expected_manifest
    assert manifest["source_input_count"] == 22
    assert manifest["source_input_paths"] == [path.as_posix() for path in gate.SOURCE_PATHS]
    assert manifest["source_input_sha256"] == {path.as_posix(): gate.SOURCE_SHA256[path] for path in gate.SOURCE_PATHS}
    assert len(manifest["source_input_verification"]) == 22
    assert [row["source_ordinal"] for row in manifest["source_input_verification"]] == list(range(1, 23))
    assert [row["source_relative_path"] for row in manifest["source_input_verification"]] == [path.as_posix() for path in gate.SOURCE_PATHS]
    assert all(row["tracked"] is row["regular"] is row["non_symlink"] is row["source_verified"] is True for row in manifest["source_input_verification"])
    assert all(row["expected_sha256"] == row["observed_sha256"] == gate.SOURCE_SHA256[gate.SOURCE_PATHS[index]] for index, row in enumerate(manifest["source_input_verification"]))
    assert manifest["source_structural_checks_before_first_content_read"] is True
    assert manifest["output_files"] == list(gate.OUTPUT_FILES) and manifest["output_file_count"] == 6
    assert manifest["output_sha256"] == output_hashes and gate.MANIFEST_FILENAME not in output_hashes
    assert manifest["residue_identity_semantics_design_frozen"] is True
    assert manifest["atom_name_semantics_design_frozen"] is True
    assert manifest["admit_004_admit_005_rule_separation_frozen"] is True
    assert manifest["truth_table_case_count"] == manifest["truth_table_passed_count"] == 16
    assert manifest["exact11_identity_atom_audit_count"] == 11
    assert manifest["exact11_identity_semantics_valid_count"] == 11
    assert manifest["exact11_atom_name_semantics_valid_count"] == 11
    assert manifest["exact11_admit_005_scope_pass_count"] == 11
    assert manifest["exact11_auth_label_conflict_count"] == 3
    assert manifest["exact11_auth_label_no_conflict_count"] == 8
    assert manifest["exact11_insertion_blocked_count"] == 11
    assert manifest["exact11_effective_blocked_count"] == 11
    assert manifest["design_frozen_pending_successor_integration_issue_count"] == 2
    assert manifest["ready_for_residue_identity_atom_name_semantics_successor_integration"] is True
    for key in (
        "residue_identity_semantics_integrated_into_effective_schema",
        "atom_name_semantics_integrated_into_effective_schema", "admit_004_rule_logic_ready",
        "admit_004_evaluator_implemented", "candidate_records_materialized",
        "ready_for_real_candidate_evaluation", "ready_for_bulk_download_now",
        "ready_for_training", "ready_to_train_now", "raw_read_current_step",
        "parser_executed_current_step", "provider_executed_current_step",
        "network_access_used_current_step", "download_attempted_current_step",
        "checkpoint_accessed_current_step", "model_or_training_code_used_current_step",
    ):
        assert manifest[key] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    all_output_hashes = {name: _sha256(root / name) for name in gate.OUTPUT_FILES}
    assert all_output_hashes == EXPECTED_OUTPUT_SHA256
    return all_output_hashes


def main() -> int:
    root = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    first = gate.run_covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate_v1(root)
    first_hashes = _validate_result(first, root)
    first_bytes = {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    first_sources = tuple(record.observed_sha256 for record in first["state"]["source_snapshot"].records)
    second = gate.run_covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate_v1(root)
    second_hashes = _validate_result(second, root)
    second_sources = tuple(record.observed_sha256 for record in second["state"]["source_snapshot"].records)
    assert first_hashes == second_hashes
    assert first_bytes == {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    assert first_sources == second_sources
    manifest = second["manifest"]
    assert manifest["all_checks_passed"] is True
    print("all_checks_passed=true")
    assert manifest["source_input_count"] == 22
    print("source_input_count=22")
    assert manifest["truth_table_passed_count"] == 16
    print("truth_table_passed_count=16")
    assert manifest["exact11_identity_atom_audit_count"] == 11
    print("exact11_identity_atom_audit_count=11")
    assert manifest["exact11_auth_label_conflict_count"] == 3 and manifest["exact11_auth_label_no_conflict_count"] == 8
    print("exact11_auth_label_conflict_split=3/8")
    assert manifest["exact11_identity_semantics_valid_count"] == 11
    print("exact11_identity_semantics_valid_count=11")
    assert manifest["exact11_atom_name_semantics_valid_count"] == 11
    print("exact11_atom_name_semantics_valid_count=11")
    assert manifest["exact11_admit_005_scope_pass_count"] == 11
    print("exact11_admit_005_scope_pass_count=11")
    assert manifest["exact11_insertion_blocked_count"] == 11
    print("exact11_insertion_blocked_count=11")
    assert manifest["ready_for_residue_identity_atom_name_semantics_successor_integration"] is True
    print("ready_for_residue_identity_atom_name_semantics_successor_integration=true")
    assert manifest["candidate_records_materialized"] is False
    print("candidate_records_materialized=false")
    assert manifest["admit_004_rule_logic_ready"] is False
    print("admit_004_rule_logic_ready=false")
    assert manifest["ready_for_real_candidate_evaluation"] is False
    print("ready_for_real_candidate_evaluation=false")
    assert manifest["ready_for_bulk_download_now"] is False
    print("ready_for_bulk_download_now=false")
    assert manifest["ready_for_training"] is False
    print("ready_for_training=false")
    assert first_hashes == second_hashes and first_sources == second_sources
    print("double_materialization_byte_identical=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
