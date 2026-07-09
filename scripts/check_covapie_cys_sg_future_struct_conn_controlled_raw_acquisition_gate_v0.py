#!/usr/bin/env python
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_cys_sg_future_struct_conn_controlled_raw_acquisition_gate as gate  # noqa: E402


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict, set)):
        return json.dumps(sorted(value) if isinstance(value, set) else value, sort_keys=True)
    return value


def atomic_write_text(path: str | Path, text: str) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, output)


def write_csv(rows: list[dict[str, Any]], path: str | Path, fieldnames: list[str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key, "")) for key in fieldnames})
    os.replace(tmp, output)


def write_json(data: Any, path: str | Path) -> None:
    atomic_write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    pairs = ", ".join(manifest["accepted_pdb_het_pairs"])
    text = f"""# CovaPIE CYS/SG Future Struct Conn Controlled Raw Acquisition Gate v0 Summary

Step 14S performs controlled raw mmCIF acquisition for the five Step 14R PDB IDs. It downloads missing files or reuses existing raw files, then records byte-level availability and integrity metadata.

This step does not parse struct_conn, does not create ready candidates, does not write sample/final/split/leakage/training artifacts, and does not train. Raw `.cif` files are written only under `data/raw/covalent_sources/covpdb/future_struct_conn_crosscheck_raw_v0/` and must remain untracked and unstaged.

raw_mmcif_expected_count: `{manifest["raw_mmcif_expected_count"]}`
raw_mmcif_available_count: `{manifest["raw_mmcif_available_count"]}`
raw_mmcif_integrity_passed_count: `{manifest["raw_mmcif_integrity_passed_count"]}`
raw_acquisition_success_count: `{manifest["raw_acquisition_success_count"]}`
raw_downloaded_current_run_count: `{manifest["raw_downloaded_current_run_count"]}`
raw_reused_existing_count: `{manifest["raw_reused_existing_count"]}`
accepted_pdb_het_pairs: `{pairs}`
struct_conn_parsed_current_step: `{manifest["struct_conn_parsed_current_step"]}`
ready_for_covapie_cys_sg_future_struct_conn_crosscheck_execution_gate: `{manifest["ready_for_covapie_cys_sg_future_struct_conn_crosscheck_execution_gate"]}`
ready_for_training: `{manifest["ready_for_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.
"""
    atomic_write_text(path, text)


def run() -> int:
    result = gate.run_covapie_cys_sg_future_struct_conn_controlled_raw_acquisition_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["request_rows"], gate.REQUEST_MANIFEST_CSV, gate.REQUEST_COLUMNS)
    write_json(result["request_rows"], gate.REQUEST_MANIFEST_JSON)
    write_csv(result["execution_rows"], gate.EXECUTION_AUDIT_CSV, gate.EXECUTION_COLUMNS)
    write_csv(result["integrity_rows"], gate.INTEGRITY_AUDIT_CSV, gate.INTEGRITY_COLUMNS)
    write_csv(result["availability_rows"], gate.AVAILABILITY_MANIFEST_CSV, gate.AVAILABILITY_COLUMNS)
    write_csv(result["policy_rows"], gate.POLICY_CONTRACT_CSV, gate.POLICY_COLUMNS)
    write_csv(result["downstream_rows"], gate.DOWNSTREAM_READINESS_CONTRACT_CSV, gate.DOWNSTREAM_COLUMNS)
    write_csv(result["safety_rows"], gate.SAFETY_AUDIT_CSV, gate.SAFETY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_cys_sg_future_struct_conn_controlled_raw_acquisition_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_cys_sg_future_struct_conn_controlled_raw_acquisition_gate_v0_blocked")
    for key in [
        "raw_mmcif_expected_count",
        "raw_mmcif_available_count",
        "raw_mmcif_integrity_passed_count",
        "raw_acquisition_success_count",
        "raw_downloaded_current_run_count",
        "raw_reused_existing_count",
        "accepted_pdb_het_pairs",
        "network_access_used_current_step",
        "download_attempted_current_step",
        "struct_conn_parsed_current_step",
        "ready_for_covapie_cys_sg_future_struct_conn_crosscheck_execution_gate",
        "ready_for_training",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
