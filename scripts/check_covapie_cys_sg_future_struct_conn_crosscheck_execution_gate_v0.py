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

from covalent_ext import covapie_cys_sg_future_struct_conn_crosscheck_execution_gate as gate  # noqa: E402


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


def write_summary(manifest: dict[str, Any], query_rows: list[dict[str, Any]], path: str | Path) -> None:
    statuses = ", ".join(f"{row['pdb_id']}/{row['expected_het_id']}={row['crosscheck_status']}" for row in query_rows)
    text = f"""# CovaPIE CYS/SG Future Struct Conn Cross-check Execution Gate v0 Summary

Step 14T reads the five Step 14S raw mmCIF files and parses `_struct_conn` with a stdlib-only parser to cross-check CYS SG to ligand HET evidence.

This step writes struct_conn evidence artifacts only. Matched records remain evidence candidates pending a result review gate; they are not ready candidates. This step does not write sample_index, final_dataset, split assignments, leakage matrices, dataloader smoke artifacts, or training artifacts, and it does not train.

crosscheck_input_count: `{manifest["crosscheck_input_count"]}`
raw_mmcif_read_count: `{manifest["raw_mmcif_read_count"]}`
struct_conn_parse_attempt_count: `{manifest["struct_conn_parse_attempt_count"]}`
struct_conn_parse_success_count: `{manifest["struct_conn_parse_success_count"]}`
matched_input_count: `{manifest["matched_input_count"]}`
unmatched_input_count: `{manifest["unmatched_input_count"]}`
ambiguous_input_count: `{manifest["ambiguous_input_count"]}`
evidence_candidate_count: `{manifest["evidence_candidate_count"]}`
crosscheck_statuses: `{statuses}`
ready_for_covapie_cys_sg_struct_conn_crosscheck_result_review_gate: `{manifest["ready_for_covapie_cys_sg_struct_conn_crosscheck_result_review_gate"]}`
ready_for_covapie_cys_sg_struct_conn_crosscheck_blocked_review_gate: `{manifest["ready_for_covapie_cys_sg_struct_conn_crosscheck_blocked_review_gate"]}`
ready_for_training: `{manifest["ready_for_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.
"""
    atomic_write_text(path, text)


def run() -> int:
    result = gate.run_covapie_cys_sg_future_struct_conn_crosscheck_execution_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["parse_rows"], gate.RAW_PARSE_AUDIT_CSV, gate.RAW_PARSE_COLUMNS)
    write_csv(result["query_rows"], gate.QUERY_EXECUTION_AUDIT_CSV, gate.QUERY_COLUMNS)
    write_csv(result["evidence_rows"], gate.MATCHED_EVIDENCE_CANDIDATES_CSV, gate.EVIDENCE_COLUMNS)
    write_json(result["evidence_rows"], gate.MATCHED_EVIDENCE_CANDIDATES_JSON)
    write_csv(result["summary_rows"], gate.RESULT_SUMMARY_CSV, gate.SUMMARY_COLUMNS)
    write_csv(result["policy_rows"], gate.POLICY_CONTRACT_CSV, gate.POLICY_COLUMNS)
    write_csv(result["downstream_rows"], gate.DOWNSTREAM_READINESS_CONTRACT_CSV, gate.DOWNSTREAM_COLUMNS)
    write_csv(result["safety_rows"], gate.SAFETY_AUDIT_CSV, gate.SAFETY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], result["query_rows"], gate.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_cys_sg_future_struct_conn_crosscheck_execution_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_cys_sg_future_struct_conn_crosscheck_execution_gate_v0_blocked")
    for key in [
        "crosscheck_input_count",
        "raw_mmcif_read_count",
        "struct_conn_parse_attempt_count",
        "struct_conn_parse_success_count",
        "matched_input_count",
        "unmatched_input_count",
        "ambiguous_input_count",
        "evidence_candidate_count",
        "ready_for_covapie_cys_sg_struct_conn_crosscheck_result_review_gate",
        "ready_for_covapie_cys_sg_struct_conn_crosscheck_blocked_review_gate",
        "ready_for_training",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
