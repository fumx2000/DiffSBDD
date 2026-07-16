#!/usr/bin/env python3
"""Fail-closed checker for CovaPIE Step14AU-E0-P6-D."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_residue_locator_real_provider_sidecar_integration_gate
    as gate,
)


_MISSING_MODULE = object()


def _forbidden_module_snapshot() -> dict[str, object]:
    return {
        name: sys.modules.get(name, _MISSING_MODULE)
        for name in gate.FORBIDDEN_RUNTIME_MODULE_NAMES
    }


def _assert_forbidden_modules_unchanged(before: Mapping[str, object]) -> None:
    for name, before_module in before.items():
        after_module = sys.modules.get(name, _MISSING_MODULE)
        if before_module is _MISSING_MODULE:
            assert after_module is _MISSING_MODULE
        else:
            assert after_module is before_module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None
        rows = [dict(row) for row in reader]
    return tuple(reader.fieldnames), rows


def _expected_csv_rows(
    columns: Sequence[str], rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    return [
        {
            column: (
                "true" if row[column] is True
                else "false" if row[column] is False
                else str(row[column])
            )
            for column in columns
        }
        for row in rows
    ]


def _validate_exact_output_set(root: Path) -> None:
    expected = set(gate.OUTPUT_FILES)
    assert root.is_dir() and not root.is_symlink()
    assert {path.name for path in root.iterdir()} == expected
    assert all((root / name).is_file() and not (root / name).is_symlink() for name in expected)
    assert not list(root.glob("*.tmp")) and not list(root.glob("*.part"))


def _validate_result(result: Mapping[str, Any], root: Path) -> dict[str, str]:
    state = result["state"]
    manifest = result["manifest"]
    assert state["all_checks_passed"] is True
    assert state["validation_failures"] == []
    assert state["source_ok"] is state["p3_ok"] is state["p6a_ok"] is state["p6c_ok"] is True
    assert state["runtime_modules_ok"] is True
    assert state["runtime_forbidden_module_delta_ok"] is True
    assert state["runtime_forbidden_module_new_import_count"] == 0
    assert state["runtime_forbidden_module_replacement_count"] == 0
    assert state["runtime_forbidden_module_deletion_count"] == 0
    assert state["runtime_module_names"] == (
        gate.P2_RUNTIME_MODULE_NAME, gate.P4_RUNTIME_MODULE_NAME,
    )
    assert len(state["source_snapshot"].records) == 19
    assert tuple(record.relative_path for record in state["source_snapshot"].records) == gate.SOURCE_PATHS
    assert all(record.observed_sha256 == gate.SOURCE_SHA256[record.relative_path] for record in state["source_snapshot"].records)
    assert state["keyed_join_count"] == 11
    assert state["secondary_identity_match_count"] == 11
    assert state["p4_recomputation_count"] == 11
    assert state["provider_five_field_match_count"] == 11
    assert gate.validate_overlay_rows(state["overlay_rows"], sys.modules[gate.P2_RUNTIME_MODULE_NAME])
    assert gate.validate_evidence_rows(state["evidence_rows"])
    assert gate.validate_contract_rows(state["contract_rows"], state["observations"])
    assert all(row["safety_passed"] is True for row in state["safety_rows"])
    assert gate.validate_issue_rows(state["issue_rows"], state["p3_source"]["issues"])

    _validate_exact_output_set(root)
    csv_specs = (
        (gate.CONTRACT_FILENAME, gate.CONTRACT_COLUMNS, state["contract_rows"]),
        (gate.OVERLAY_FILENAME, gate.OVERLAY_COLUMNS, state["overlay_rows"]),
        (gate.EVIDENCE_FILENAME, gate.EVIDENCE_COLUMNS, state["evidence_rows"]),
        (gate.SAFETY_FILENAME, gate.SAFETY_COLUMNS, state["safety_rows"]),
        (gate.ISSUE_FILENAME, gate.ISSUE_COLUMNS, state["issue_rows"]),
    )
    for filename, columns, rows in csv_specs:
        header, disk_rows = _read_csv(root / filename)
        assert header == tuple(columns)
        assert disk_rows == _expected_csv_rows(columns, rows)

    output_hashes = {name: _sha256(root / name) for name in gate.CSV_OUTPUTS}
    expected_manifest = gate._manifest_payload(state, output_hashes)
    disk_manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest == disk_manifest == expected_manifest
    assert manifest["output_files"] == list(gate.OUTPUT_FILES)
    assert manifest["output_file_count"] == 6
    assert manifest["output_sha256"] == output_hashes
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]
    assert manifest["p3_schema_validated"] is True
    assert manifest["target_binding_count"] == 11
    assert manifest["predecessor_sidecar_count"] == 11
    assert manifest["keyed_join_count"] == 11
    assert manifest["secondary_identity_match_count"] == 11
    assert manifest["p4_recomputation_count"] == 11
    assert manifest["provider_five_field_match_count"] == 11
    assert manifest["overlay_column_count"] == 6 and manifest["overlay_row_count"] == 11
    assert manifest["evidence_audit_passed_count"] == 11
    assert manifest["unknown_insertion_integrated_count"] == 11
    assert manifest["admit_004_blocking_overlay_count"] == 11
    assert manifest["provider_source_id_valid_count"] == 11
    assert manifest["provider_source_id_unique_count"] == 11
    assert manifest["provider_sha_valid_count"] == 11
    assert manifest["provider_sha_unique_count"] == 11
    assert manifest["real_provider_sidecar_integration_gate_passed"] is True
    assert manifest["real_provider_sidecar_integrated_into_additive_overlay"] is True
    assert manifest["five_locator_fields_integrated_row_count"] == 11
    assert manifest["provider_provenance_available_count"] == 11
    assert manifest["candidate_records_materialized"] is False
    assert manifest["admission_records_modified"] is False
    assert manifest["real_samples_backfilled"] == 0
    for key in (
        "admit_004_rule_logic_ready",
        "ready_for_e1_residue_identity_semantics_design",
        "ready_for_real_candidate_evaluation", "ready_for_bulk_download_now",
        "ready_for_training", "ready_to_train_now",
    ):
        assert manifest[key] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["resolved_predecessor_issue_ids"] == [gate.RESOLVED_PREDECESSOR_ISSUE_ID]
    assert manifest["active_issue_count"] == 11
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    assert manifest["raw_read_current_step"] is False
    assert manifest["parser_executed_current_step"] is False
    assert manifest["network_access_used_current_step"] is False
    assert manifest["download_attempted_current_step"] is False
    assert manifest["model_or_training_code_used_current_step"] is False
    return {name: _sha256(root / name) for name in gate.OUTPUT_FILES}


def main() -> int:
    root = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    before_forbidden = _forbidden_module_snapshot()
    first = gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_provider_sidecar_integration_gate_v1(root)
    _assert_forbidden_modules_unchanged(before_forbidden)
    first_hashes = _validate_result(first, root)
    first_bytes = {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    first_sources = tuple(record.observed_sha256 for record in first["state"]["source_snapshot"].records)
    before_second = _forbidden_module_snapshot()
    second = gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_provider_sidecar_integration_gate_v1(root)
    _assert_forbidden_modules_unchanged(before_second)
    second_hashes = _validate_result(second, root)
    second_sources = tuple(record.observed_sha256 for record in second["state"]["source_snapshot"].records)
    assert first_hashes == second_hashes
    assert first_bytes == {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    assert first_sources == second_sources
    assert not list(root.glob("*.tmp")) and not list(root.glob("*.part"))

    manifest = second["manifest"]
    assert manifest["real_provider_sidecar_integration_gate_passed"] is True
    print("real_provider_sidecar_integration_gate_passed=true")
    assert manifest["source_input_count"] == 19
    print("source_input_count=19")
    assert manifest["p3_schema_validated"] is True
    print("p3_schema_validated=true")
    assert manifest["keyed_join_count"] == 11
    print("keyed_join_count=11")
    assert manifest["secondary_identity_match_count"] == 11
    print("secondary_identity_match_count=11")
    assert manifest["p4_recomputation_count"] == 11
    print("p4_recomputation_count=11")
    assert manifest["overlay_row_count"] == 11 and manifest["overlay_column_count"] == 6
    print("overlay_shape=11x6")
    assert manifest["evidence_audit_passed_count"] == 11
    print("evidence_audit_passed_count=11")
    assert manifest["unknown_insertion_integrated_count"] == 11
    print("unknown_insertion_integrated_count=11")
    assert manifest["admit_004_blocking_overlay_count"] == 11
    print("admit_004_blocking_overlay_count=11")
    assert manifest["candidate_records_materialized"] is False
    print("candidate_records_materialized=false")
    assert manifest["admit_004_rule_logic_ready"] is False
    print("admit_004_rule_logic_ready=false")
    assert manifest["ready_for_e1_residue_identity_semantics_design"] is False
    print("ready_for_e1_residue_identity_semantics_design=false")
    assert manifest["ready_for_real_candidate_evaluation"] is False
    print("ready_for_real_candidate_evaluation=false")
    assert manifest["ready_for_bulk_download_now"] is False
    print("ready_for_bulk_download_now=false")
    assert manifest["ready_for_training"] is False
    print("ready_for_training=false")
    assert first_hashes == second_hashes
    print("double_materialization_byte_identical=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
