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

from covalent_ext import covapie_cys_sg_future_struct_conn_crosscheck_gate as gate  # noqa: E402


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
    text = f"""# CovaPIE CYS/SG Future Struct Conn Cross-Check Gate v0 Summary

Step 14R creates the future struct_conn cross-check design contracts for the five Step 14Q inputs.

This step does not download raw/mmCIF files, does not read raw/mmCIF files, does not parse struct_conn, does not create ready candidates, does not write sample/final/split/leakage/training artifacts, and does not train.

future_struct_conn_crosscheck_input_count: `{manifest["future_struct_conn_crosscheck_input_count"]}`
expected_struct_conn_query_plan_count: `{manifest["expected_struct_conn_query_plan_count"]}`
expected_raw_mmcif_acquisition_plan_count: `{manifest["expected_raw_mmcif_acquisition_plan_count"]}`
accepted_pdb_het_pairs: `{pairs}`
raw_downloaded_current_step: `{manifest["raw_downloaded_current_step"]}`
raw_mmcif_read_current_step: `{manifest["raw_mmcif_read_current_step"]}`
struct_conn_parsed_current_step: `{manifest["struct_conn_parsed_current_step"]}`
ready_candidate_count_current_step: `{manifest["ready_candidate_count_current_step"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_for_covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_acquisition_gate: `{manifest["ready_for_covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_acquisition_gate"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

The next allowed step is a controlled raw acquisition gate. Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.
"""
    atomic_write_text(path, text)


def run() -> int:
    result = gate.run_covapie_cys_sg_future_struct_conn_crosscheck_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["input_contract_rows"], gate.INPUT_CONTRACT_CSV, gate.INPUT_CONTRACT_COLUMNS)
    write_csv(result["query_plan_rows"], gate.QUERY_PLAN_CSV, gate.QUERY_PLAN_COLUMNS)
    write_json(result["query_plan_rows"], gate.QUERY_PLAN_JSON)
    write_csv(result["raw_acquisition_rows"], gate.RAW_ACQUISITION_PLAN_CSV, gate.RAW_ACQUISITION_COLUMNS)
    write_csv(result["acceptance_rows"], gate.EVIDENCE_ACCEPTANCE_CONTRACT_CSV, gate.ACCEPTANCE_COLUMNS)
    write_csv(result["blocking_rows"], gate.BLOCKING_REASONS_CONTRACT_CSV, gate.BLOCKING_COLUMNS)
    write_csv(result["downstream_rows"], gate.DOWNSTREAM_READINESS_CONTRACT_CSV, gate.DOWNSTREAM_COLUMNS)
    write_csv(result["safety_rows"], gate.SAFETY_AUDIT_CSV, gate.SAFETY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_cys_sg_future_struct_conn_crosscheck_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_cys_sg_future_struct_conn_crosscheck_gate_v0_blocked")
    for key in [
        "future_struct_conn_crosscheck_input_count",
        "expected_struct_conn_query_plan_count",
        "expected_raw_mmcif_acquisition_plan_count",
        "accepted_pdb_het_pairs",
        "raw_downloaded_current_step",
        "raw_mmcif_read_current_step",
        "struct_conn_parsed_current_step",
        "ready_candidate_count_current_step",
        "ready_for_covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_acquisition_gate",
        "ready_for_training",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
