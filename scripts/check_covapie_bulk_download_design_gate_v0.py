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

from covalent_ext import covapie_bulk_download_design_gate as design_gate  # noqa: E402


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
    text = f"""# CovaPIE Bulk Download Design Gate v0 Summary

Step 14B is a design gate for future small, medium, and bulk structure downloads.
It does not use the network, download files, write raw structures, write download manifest rows, read raw content, parse mmCIF, extract coordinates, write actual dataloader smoke, write final datasets, write sample indexes, write split assignments, write leakage matrices, import torch or numpy, load checkpoints, run model forward, compute loss, or train.

The next step is `covapie_small_pilot_download_manifest_gate`, not actual download smoke, not actual dataloader smoke, and not training.
Raw files must remain untracked and uncommitted.
The five canonical mask tasks are preserved, including `scaffold_only / B3`.
`feature_semantics_known_for_training=false` and `unknown_atom_feature_policy_finalized_for_training=false` remain unchanged.
Formal training, fine-tuning, or real parameter updates still require a separate feature semantics audit and leakage/split design gate.

candidate_source_contract_row_count: `{manifest["candidate_source_contract_row_count"]}`
candidate_source_contract_passed: `{manifest["candidate_source_contract_passed"]}`
storage_layout_contract_row_count: `{manifest["storage_layout_contract_row_count"]}`
storage_layout_contract_passed: `{manifest["storage_layout_contract_passed"]}`
download_manifest_schema_contract_row_count: `{manifest["download_manifest_schema_contract_row_count"]}`
download_manifest_schema_contract_passed: `{manifest["download_manifest_schema_contract_passed"]}`
network_boundary_contract_row_count: `{manifest["network_boundary_contract_row_count"]}`
network_boundary_contract_passed: `{manifest["network_boundary_contract_passed"]}`
pilot_scale_contract_row_count: `{manifest["pilot_scale_contract_row_count"]}`
pilot_scale_contract_passed: `{manifest["pilot_scale_contract_passed"]}`
resume_checksum_contract_row_count: `{manifest["resume_checksum_contract_row_count"]}`
resume_checksum_contract_passed: `{manifest["resume_checksum_contract_passed"]}`
failure_taxonomy_contract_row_count: `{manifest["failure_taxonomy_contract_row_count"]}`
failure_taxonomy_contract_passed: `{manifest["failure_taxonomy_contract_passed"]}`
safety_audit_passed: `{manifest["safety_audit_passed"]}`
ready_for_covapie_small_pilot_download_manifest_gate: `{manifest["ready_for_covapie_small_pilot_download_manifest_gate"]}`
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
    result = design_gate.run_covapie_bulk_download_design_gate_v0()
    write_csv(result["precondition_rows"], design_gate.PRECONDITION_AUDIT_CSV, design_gate.PRECONDITION_COLUMNS)
    write_csv(result["candidate_rows"], design_gate.CANDIDATE_SOURCE_CONTRACT_CSV, design_gate.CANDIDATE_SOURCE_COLUMNS)
    write_csv(result["storage_rows"], design_gate.STORAGE_LAYOUT_CONTRACT_CSV, design_gate.STORAGE_LAYOUT_COLUMNS)
    write_csv(result["schema_rows"], design_gate.MANIFEST_SCHEMA_CONTRACT_CSV, design_gate.MANIFEST_SCHEMA_COLUMNS)
    write_csv(result["network_rows"], design_gate.NETWORK_BOUNDARY_CONTRACT_CSV, design_gate.NETWORK_BOUNDARY_COLUMNS)
    write_csv(result["pilot_rows"], design_gate.PILOT_SCALE_CONTRACT_CSV, design_gate.PILOT_SCALE_COLUMNS)
    write_csv(result["resume_rows"], design_gate.RESUME_CHECKSUM_CONTRACT_CSV, design_gate.RESUME_CHECKSUM_COLUMNS)
    write_csv(result["failure_rows"], design_gate.FAILURE_TAXONOMY_CONTRACT_CSV, design_gate.FAILURE_TAXONOMY_COLUMNS)
    write_csv(result["safety_rows"], design_gate.SAFETY_AUDIT_CSV, design_gate.SAFETY_COLUMNS)
    write_json(result["manifest"], design_gate.MANIFEST_JSON)
    write_summary(result["manifest"], design_gate.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_bulk_download_design_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_bulk_download_design_gate_v0_blocked")
    for key in [
        "candidate_source_contract_row_count",
        "candidate_source_contract_passed",
        "storage_layout_contract_row_count",
        "storage_layout_contract_passed",
        "download_manifest_schema_contract_row_count",
        "download_manifest_schema_contract_passed",
        "network_boundary_contract_row_count",
        "network_boundary_contract_passed",
        "pilot_scale_contract_row_count",
        "pilot_scale_contract_passed",
        "resume_checksum_contract_row_count",
        "resume_checksum_contract_passed",
        "failure_taxonomy_contract_row_count",
        "failure_taxonomy_contract_passed",
        "network_access_used",
        "download_attempted",
        "raw_files_written_current_step",
        "raw_file_content_read_current_step",
        "ready_for_covapie_small_pilot_download_manifest_gate",
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
