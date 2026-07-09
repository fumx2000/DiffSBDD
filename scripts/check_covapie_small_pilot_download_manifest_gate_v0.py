#!/usr/bin/env python
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_small_pilot_download_manifest_gate as gate  # noqa: E402


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict, set)):
        return json.dumps(sorted(value) if isinstance(value, set) else value, sort_keys=True)
    return value


def write_csv(rows: list[dict[str, Any]], path: str | Path, fieldnames: list[str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key, "")) for key in fieldnames})


def write_json(data: Any, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# CovaPIE Small Pilot Download Manifest Gate v0 Summary

Step 14C writes source-profile-specific small pilot download manifest metadata.
It keeps `current_execution_source_specific=true` while preserving cross-source schema fields for future source registry and resolver contracts.
It does not use the network, download files, write raw structures, read raw content, parse mmCIF, extract coordinates, write actual dataloader smoke, write final datasets, write sample indexes, write split assignments, write leakage matrices, import torch or numpy, load checkpoints, run model forward, compute loss, or train.

The current profile is `{manifest["current_source_profile"]}` for `{manifest["current_source_database"]}`.
Because selected eligible event-level candidates are `{manifest["selected_small_pilot_row_count"]}`, `ready_for_covapie_small_pilot_download_smoke` is `{manifest["ready_for_covapie_small_pilot_download_smoke"]}`.
If fewer than 20 qualified candidates are selected, the next step is candidate expansion rather than download smoke.

current_source_profile: `{manifest["current_source_profile"]}`
current_source_database: `{manifest["current_source_database"]}`
cross_source_generalization_supported_by_schema: `{manifest["cross_source_generalization_supported_by_schema"]}`
current_execution_source_specific: `{manifest["current_execution_source_specific"]}`
pdb_wide_blind_scan_allowed: `{manifest["pdb_wide_blind_scan_allowed"]}`
selected_small_pilot_row_count: `{manifest["selected_small_pilot_row_count"]}`
insufficient_candidate_count_for_20_to_50_pilot: `{manifest["insufficient_candidate_count_for_20_to_50_pilot"]}`
source_profile_contract_passed: `{manifest["source_profile_contract_passed"]}`
candidate_selection_audit_passed: `{manifest["candidate_selection_audit_passed"]}`
manifest_schema_validation_audit_passed: `{manifest["manifest_schema_validation_audit_passed"]}`
network_boundary_audit_passed: `{manifest["network_boundary_audit_passed"]}`
readiness_contract_passed: `{manifest["readiness_contract_passed"]}`
safety_audit_passed: `{manifest["safety_audit_passed"]}`
ready_for_covapie_small_pilot_download_smoke: `{manifest["ready_for_covapie_small_pilot_download_smoke"]}`
ready_for_covapie_bulk_download_smoke: `{manifest["ready_for_covapie_bulk_download_smoke"]}`
ready_for_covapie_actual_dataloader_adapter_smoke: `{manifest["ready_for_covapie_actual_dataloader_adapter_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
blocking_reasons: `{manifest["blocking_reasons"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.run_covapie_small_pilot_download_manifest_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["source_profile_rows"], gate.SOURCE_PROFILE_CONTRACT_CSV, gate.SOURCE_PROFILE_COLUMNS)
    write_csv(result["candidate_rows"], gate.CANDIDATE_SELECTION_AUDIT_CSV, gate.CANDIDATE_SELECTION_COLUMNS)
    write_csv(result["small_pilot_rows"], gate.SMALL_PILOT_MANIFEST_CSV, gate.SMALL_PILOT_MANIFEST_COLUMNS)
    write_json(result["small_pilot_rows"], gate.SMALL_PILOT_MANIFEST_JSON)
    write_csv(result["schema_rows"], gate.SCHEMA_VALIDATION_AUDIT_CSV, gate.SCHEMA_VALIDATION_COLUMNS)
    write_csv(result["network_rows"], gate.NETWORK_BOUNDARY_AUDIT_CSV, gate.NETWORK_BOUNDARY_COLUMNS)
    write_csv(result["readiness_rows"], gate.READINESS_CONTRACT_CSV, gate.READINESS_COLUMNS)
    write_csv(result["safety_rows"], gate.SAFETY_AUDIT_CSV, gate.SAFETY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_small_pilot_download_manifest_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_small_pilot_download_manifest_gate_v0_blocked")
    for key in [
        "current_source_profile",
        "current_source_database",
        "cross_source_generalization_supported_by_schema",
        "current_execution_source_specific",
        "pdb_wide_blind_scan_allowed",
        "small_pilot_download_manifest_row_count",
        "selected_small_pilot_row_count",
        "insufficient_candidate_count_for_20_to_50_pilot",
        "source_profile_contract_row_count",
        "source_profile_contract_passed",
        "candidate_selection_audit_passed",
        "manifest_schema_validation_audit_row_count",
        "manifest_schema_validation_audit_passed",
        "network_boundary_audit_row_count",
        "network_boundary_audit_passed",
        "readiness_contract_row_count",
        "readiness_contract_passed",
        "network_access_used",
        "download_attempted",
        "raw_files_written_current_step",
        "raw_file_content_read_current_step",
        "ready_for_covapie_small_pilot_download_smoke",
        "ready_for_covapie_bulk_download_smoke",
        "ready_for_covapie_actual_dataloader_adapter_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
