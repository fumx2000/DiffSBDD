#!/usr/bin/env python3
"""Fail-closed checker for CovaPIE Step14AU-E0-P6-C."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke
    as gate,
)

EXPECTED_OUTPUT_SHA256 = {
    gate.CONTRACT_FILENAME: "82f3f225cb2e18ba19ff386e612670279ebcdf4a0435b7b4642ff8167ccb09b7",
    gate.SIDECAR_FILENAME: "066c0beeaa01d31a6d6ea3fae62f3df5177c2d904f6295646ee33a7fcd780ac7",
    gate.EVIDENCE_FILENAME: "4048efdfe373fe955995ded43639fcbd7baf67560e867662dbd18fe22a4fb1ab",
    gate.SAFETY_FILENAME: "e7736e3567d6ef76d19b13f46741f297000ea130644dd8b8b4b653b9a04bc6dc",
    gate.ISSUE_FILENAME: "5bda40b683d649fb28a2172291f329c1f87d10f3a2bd122e1d5a6ab887a071c4",
    gate.MANIFEST_FILENAME: "9061e36c333cf498dd5844407f5df11d64c3e271ae47e407938d34ac851d3aab",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None
        return tuple(reader.fieldnames), list(reader)


def _csv_text(value: object) -> str:
    if type(value) is bool:
        return "true" if value else "false"
    return str(value)


def _expected_csv_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [{key: _csv_text(value) for key, value in row.items()} for row in rows]


def _validate_result(result: Mapping[str, Any], root: Path) -> None:
    state = result["state"]
    manifest = result["manifest"]
    assert state["all_checks_passed"] is True
    assert state["validation_failures"] == []
    assert state["source_ok"] is True
    assert state["predecessor_ok"] is True
    assert len(state["joined_rows"]) == 11
    assert state["schema_ok"] is True
    assert state["extracted_schemas"] == {
        "p6a_future_real_sidecar_columns": gate.FUTURE_REAL_SIDECAR_COLUMNS,
        "p6a_binding_columns": gate.P6A_BINDING_COLUMNS,
        "p6b_matrix_columns": gate.P6B_MATRIX_COLUMNS,
    }
    assert state["runtime_modules_ok"] is True
    assert state["runtime_module_names"] == (
        gate.P4_RUNTIME_MODULE_NAME, gate.P5B_RUNTIME_MODULE_NAME,
    )
    assert all(name not in sys.modules for name in gate.FORBIDDEN_RUNTIME_MODULE_NAMES)
    assert state["modules_ok"] is True
    # These are exact11 execute_one_binding counters, not totals for P5-B's
    # existing import-time synthetic self-checks or the whole Python process.
    assert state["counters"] == {
        "raw": 11, "decode": 11, "struct_parse": 11,
        "atom_parse": 11, "provider": 11,
    }
    assert state["sidecar_shape_valid"] is True
    assert len(state["sidecar_rows"]) == 11
    assert all(tuple(row) == gate.FUTURE_REAL_SIDECAR_COLUMNS for row in state["sidecar_rows"])
    assert state["exported_pass_count"] + state["exported_blocking_count"] == 11
    assert state["rejected_count"] == 0
    assert state["provider_row_count"] == 11
    assert len(set(state["source_ids"])) == 11
    assert len(state["provenance_hashes"]) == len(set(state["provenance_hashes"])) == 11
    assert all(gate._valid_sha(value) for value in state["provenance_hashes"])
    assert state["evidence_audit_passed"] is True
    assert all(row["contract_passed"] is True for row in state["contract_rows"])
    assert all(row["safety_passed"] is True for row in state["safety_rows"])

    expected_set = set(gate.OUTPUT_FILES)
    assert root.is_dir() and not root.is_symlink()
    assert {path.name for path in root.iterdir()} == expected_set
    assert all((root / name).is_file() and not (root / name).is_symlink() for name in expected_set)
    csv_specs = (
        (gate.CONTRACT_FILENAME, gate.CONTRACT_COLUMNS, state["contract_rows"]),
        (gate.SIDECAR_FILENAME, gate.FUTURE_REAL_SIDECAR_COLUMNS, state["sidecar_rows"]),
        (gate.EVIDENCE_FILENAME, gate.EVIDENCE_COLUMNS, state["evidence_rows"]),
        (gate.SAFETY_FILENAME, gate.SAFETY_COLUMNS, state["safety_rows"]),
        (gate.ISSUE_FILENAME, gate.ISSUE_COLUMNS, state["issue_rows"]),
    )
    for filename, columns, rows in csv_specs:
        header, disk_rows = _read_csv(root / filename)
        assert header == tuple(columns)
        assert disk_rows == _expected_csv_rows(rows)
    output_hashes = {name: _sha256(root / name) for name in gate.CSV_OUTPUTS}
    expected_manifest = gate._manifest_payload(state, output_hashes)
    disk_manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest == disk_manifest == expected_manifest
    assert {
        name: _sha256(root / name) for name in gate.OUTPUT_FILES
    } == EXPECTED_OUTPUT_SHA256
    assert manifest["output_files"] == list(gate.OUTPUT_FILES)
    assert manifest["output_file_count"] == 6
    assert manifest["sidecar_column_count"] == 41
    assert manifest["sidecar_row_count"] == 11
    assert manifest["rejected_count"] == 0
    assert manifest["provider_row_count"] == 11
    assert manifest["real_provider_export_execution_smoke_passed"] is True
    assert manifest["real_provider_rows_materialized_current_step"] is True
    assert manifest["ready_for_real_provider_sidecar_integration"] is True
    assert manifest["insertion_code_provenance_export_ready_for_real_samples"] is True
    for key in (
        "admit_004_rule_logic_ready",
        "ready_for_e1_residue_identity_semantics_design",
        "ready_for_real_candidate_evaluation",
        "ready_for_bulk_download_now",
        "ready_for_training",
        "ready_to_train_now",
    ):
        assert manifest[key] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["admission_records_modified_current_step"] is False
    assert manifest["real_samples_backfilled_current_step"] == 0
    assert manifest["raw_files_modified_current_step"] is False
    assert manifest["network_access_used_current_step"] is False
    assert manifest["download_attempted_current_step"] is False


def main() -> None:
    root = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    assert all(name not in sys.modules for name in gate.FORBIDDEN_RUNTIME_MODULE_NAMES)
    tracked_before = gate._git(("diff", "--name-only"), REPO_ROOT).stdout
    staged_before = gate._git(("diff", "--cached", "--name-only"), REPO_ROOT).stdout
    first = gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1()
    _validate_result(first, root)
    first_bytes = {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    first_stdout_data = {
        "source": tuple(record.sha256 for record in first["state"]["source_snapshot"].records),
        "raw": tuple(row["observed_raw_sha256"] for row in first["state"]["sidecar_rows"]),
    }
    second = gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1()
    _validate_result(second, root)
    second_bytes = {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    second_stdout_data = {
        "source": tuple(record.sha256 for record in second["state"]["source_snapshot"].records),
        "raw": tuple(row["observed_raw_sha256"] for row in second["state"]["sidecar_rows"]),
    }
    assert first_bytes == second_bytes
    assert first_stdout_data == second_stdout_data
    assert all(name not in sys.modules for name in gate.FORBIDDEN_RUNTIME_MODULE_NAMES)
    assert gate._git(("diff", "--name-only"), REPO_ROOT).stdout == tracked_before == ""
    assert gate._git(("diff", "--cached", "--name-only"), REPO_ROOT).stdout == staged_before == ""
    assert not any(path.suffix in (".tmp", ".part") for path in root.iterdir())

    manifest = second["manifest"]
    assert manifest["all_checks_passed"] is True
    print("all_checks_passed=true")
    assert manifest["source_input_count"] == 11
    print("source_input_count=11")
    assert manifest["binding_count"] == 11
    print("binding_count=11")
    assert manifest["secure_raw_read_count"] == 11
    print("secure_raw_read_count=11")
    assert manifest["strict_decode_count"] == 11
    print("strict_decode_count=11")
    assert manifest["struct_conn_parse_count"] == manifest["atom_site_parse_count"] == 11
    print("struct_conn_parse_count=11")
    print("atom_site_parse_count=11")
    assert manifest["provider_call_count"] == manifest["provider_row_count"] == 11
    print("provider_call_count=11")
    print("provider_row_count=11")
    assert manifest["sidecar_column_count"] == 41 and manifest["sidecar_row_count"] == 11
    print("sidecar_shape=41x11")
    assert manifest["rejected_count"] == 0
    print(f"exported_pass_count={manifest['exported_pass_count']}")
    print(f"exported_blocking_count={manifest['exported_blocking_count']}")
    print("rejected_count=0")
    assert manifest["present_insertion_count"] + manifest["absent_insertion_count"] + manifest["unknown_insertion_count"] == 11
    print(f"present_insertion_count={manifest['present_insertion_count']}")
    print(f"absent_insertion_count={manifest['absent_insertion_count']}")
    print(f"unknown_insertion_count={manifest['unknown_insertion_count']}")
    assert manifest["ready_for_real_provider_sidecar_integration"] is True
    print("ready_for_real_provider_sidecar_integration=true")
    assert manifest["admit_004_rule_logic_ready"] is False
    print("admit_004_rule_logic_ready=false")
    assert manifest["ready_for_e1_residue_identity_semantics_design"] is False
    print("ready_for_e1_residue_identity_semantics_design=false")
    assert manifest["ready_for_real_candidate_evaluation"] is False
    print("ready_for_real_candidate_evaluation=false")
    assert manifest["ready_for_bulk_download_now"] is False
    print("ready_for_bulk_download_now=false")
    assert manifest["ready_for_training"] is manifest["ready_to_train_now"] is False
    print("ready_for_training=false")
    print("ready_to_train_now=false")
    assert first_bytes == second_bytes and first_stdout_data == second_stdout_data
    print("p6c_outputs_and_raw_sha_twice_stable=true")


if __name__ == "__main__":
    main()
