#!/usr/bin/env python3
"""Fail-closed checker for the Step14AU-E1-B committed-metadata overlay."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate as gate,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path, columns: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert tuple(reader.fieldnames or ()) == columns
        rows = list(reader)
    assert all(tuple(row) == columns and all(value is not None for value in row.values()) for row in rows)
    return rows


def _as_csv_rows(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {key: "true" if value is True else "false" if value is False else str(value) for key, value in row.items()}
        for row in rows
    ]


def main() -> int:
    output_root = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    assert output_root.is_dir() and not output_root.is_symlink()
    names = sorted(path.name for path in output_root.iterdir())
    assert names == sorted(gate.OUTPUT_FILES)
    assert all((output_root / name).is_file() and not (output_root / name).is_symlink() for name in names)

    snapshot = gate.build_frozen_source_snapshot()
    assert gate.validate_frozen_source_snapshot(snapshot)
    state = gate.build_integration_state(snapshot)
    assert state["source_ok"] is True and state["p3_ok"] is True and state["e1a_ok"] is True
    assert state["all_checks_passed"] is True and state["validation_failures"] == []

    output_specs = (
        (gate.RULE_FILENAME, gate.RULE_COLUMNS, state["rule_rows"]),
        (gate.FIELD_FILENAME, gate.FIELD_COLUMNS, state["field_rows"]),
        (gate.CONTEXT_FILENAME, gate.CONTEXT_COLUMNS, state["context_rows"]),
        (gate.SAFETY_FILENAME, gate.SAFETY_COLUMNS, state["safety_rows"]),
        (gate.ISSUE_FILENAME, gate.ISSUE_COLUMNS, state["issue_rows"]),
    )
    for filename, columns, expected in output_specs:
        assert _csv(output_root / filename, columns) == _as_csv_rows(expected)

    hashes = {name: _sha256(output_root / name) for name in gate.CSV_OUTPUTS}
    manifest_path = output_root / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest == gate._manifest_payload(state, hashes)
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]
    assert manifest["source_input_paths"] == [path.as_posix() for path in gate.SOURCE_PATHS]
    assert manifest["source_input_sha256"] == {path.as_posix(): gate.SOURCE_SHA256[path] for path in gate.SOURCE_PATHS}
    assert manifest["integrated_rule_count"] == 15
    assert manifest["integrated_field_count"] == 22
    assert manifest["integrated_context_count"] == 18
    assert manifest["active_issue_count"] == 10
    assert manifest["semantics_complete_rule_count"] == 6
    assert manifest["implementation_semantics_complete_field_count"] == 11
    assert manifest["implementation_ready_context_count"] == 8
    assert manifest["resolved_issue_ids"] == [gate.ATOM_ISSUE]
    assert manifest["exact11_identity_atom_audit_count"] == 11
    assert manifest["exact11_identity_semantics_valid_count"] == 11
    assert manifest["exact11_atom_name_semantics_valid_count"] == 11
    assert manifest["exact11_admit_005_scope_pass_count"] == 11
    assert manifest["exact11_auth_label_conflict_count"] == 3
    assert manifest["exact11_auth_label_no_conflict_count"] == 8
    assert manifest["exact11_insertion_unknown_empty_count"] == 11
    assert manifest["exact11_insertion_blocked_count"] == 11
    assert manifest["exact11_effective_blocked_count"] == 11
    assert manifest["partial_successor_integration_applied"] is True
    assert manifest["admit_005_rule_logic_ready"] is True
    assert manifest["residue_identity_semantics_integrated_into_effective_schema"] is False
    assert manifest["covalent_residue_identity_contract_fully_integrated"] is False
    assert manifest["admit_004_rule_logic_ready"] is False
    assert manifest["ready_for_admit_004_rule_logic_implementation"] is False
    assert manifest["admit_004_evaluator_implemented"] is False
    assert manifest["candidate_records_materialized"] is False
    assert manifest["ready_for_real_candidate_evaluation"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False and manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP

    rules = _csv(output_root / gate.RULE_FILENAME, gate.RULE_COLUMNS)
    fields = _csv(output_root / gate.FIELD_FILENAME, gate.FIELD_COLUMNS)
    contexts = _csv(output_root / gate.CONTEXT_FILENAME, gate.CONTEXT_COLUMNS)
    issues = _csv(output_root / gate.ISSUE_FILENAME, gate.ISSUE_COLUMNS)
    p3_rules = list(gate._csv_document(snapshot, gate.P3_RULE_PATH).rows)
    p3_fields = list(gate._csv_document(snapshot, gate.P3_FIELD_PATH).rows)
    p3_contexts = list(gate._csv_document(snapshot, gate.P3_CONTEXT_PATH).rows)
    assert gate._unchanged_except(rules, p3_rules, "admission_rule_id", {"ADMIT_004", "ADMIT_005"}, {
        "semantics_complete", "deterministic_evaluation_possible_now", "deterministic_evaluation_possible_after_contract_freeze",
        "implementation_disposition", "blocking_reasons", "integration_source_stage", "integration_applied", "integration_reason",
    })
    assert gate._unchanged_except(fields, p3_fields, "field_name", set(gate.TARGET_FIELDS), {
        "allowed_values_defined", "normalization_defined", "exact_validation_defined", "implementation_semantics_complete",
        "semantics_evidence", "blocking_reasons", "integration_source_stage", "integration_applied", "integration_reason",
    })
    assert gate._unchanged_except(contexts, p3_contexts, "context_item", {"covalent_residue_identity_contract"}, {
        "deterministic_now", "deterministic_after_contract_freeze", "exact_contract_defined", "implementation_ready",
        "blocking_reasons", "integration_source_stage", "integration_applied", "integration_reason",
    })
    field_map = {row["field_name"]: row for row in fields}
    p3_field_map = {row["field_name"]: row for row in p3_fields}
    assert all(field_map[name] == p3_field_map[name] for name in gate.LOCATOR_FIELDS)
    assert field_map["covalent_residue_insertion_code"]["implementation_semantics_complete"] == "false"
    assert [row["issue_id"] for row in issues] == manifest["remaining_issue_ids"]
    assert gate.ATOM_ISSUE not in {row["issue_id"] for row in issues}
    assert not any(path.suffix in (".tmp", ".part") for path in output_root.iterdir())

    with tempfile.TemporaryDirectory(prefix="covapie_e1b_checker_") as temp:
        rerun_root = Path(temp) / "out"
        gate.run_covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate_v1(rerun_root)
        assert all((rerun_root / name).read_bytes() == (output_root / name).read_bytes() for name in gate.OUTPUT_FILES)

    for key, value in (
        ("all_checks_passed", "true"), ("source_count", "12"),
        ("integrated_counts", "15/22/18/10"), ("complete_ready_counts", "6/11/8"),
        ("exact11_blocked", "11/11"), ("admit_005_rule_logic_ready", "true"),
        ("admit_004_rule_logic_ready", "false"), ("ready_for_bulk_download_now", "false"),
        ("ready_for_training", "false"), ("deterministic_outputs", "true"),
    ):
        assert value
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
